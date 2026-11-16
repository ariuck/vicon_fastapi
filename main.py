import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# -------------------------------------
# 1. 프로젝트 경로 설정
# -------------------------------------

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def list_glb_files():
    """assets 폴더 안의 .glb 파일 이름 목록 (이름순)"""
    return sorted(p.name for p in ASSETS_DIR.glob("*.glb") if p.is_file())


def is_valid_glb(name):
    """assets 폴더에 실제로 있는 .glb 파일 이름인지 확인 (경로 조작 방지)"""
    return (
        isinstance(name, str)
        and name == Path(name).name
        and name.lower().endswith(".glb")
        and (ASSETS_DIR / name).is_file()
    )

# -------------------------------------
# 2. FastAPI 생성
# -------------------------------------

app = FastAPI(title="VICON Three.js Viewer")

# GLB 파일을 브라우저에 제공
app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets",
)

# -------------------------------------
# 3. 메인 화면 제공
# -------------------------------------

@app.get("/")
def index():
    return FileResponse(
        BASE_DIR / "index.html",
        media_type="text/html",
    )


# -------------------------------------
# 4. 서버 및 GLB 파일 확인
# -------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "glb_count": len(list_glb_files()),
    }


# assets 폴더의 GLB 목록을 화면에 제공
@app.get("/api/assets")
def assets():
    return {"files": list_glb_files()}


# -------------------------------------
# 5. 추출한 3D JSON 저장
# -------------------------------------

@app.post("/api/save-json")
async def save_json(request: Request):
    data = await request.json()

    if (
        not isinstance(data, dict)
        or not is_valid_glb(data.get("source_glb"))
    ):
        raise HTTPException(
            status_code=400,
            detail="assets 폴더에 없는 GLB 파일명입니다.",
        )

    # 예: 261111_D002_T001_LHY.glb → 261111_D002_T001_LHY_3d.json
    JSON_FILENAME = Path(data["source_glb"]).stem + "_3d.json"

    frames = data.get("frames")

    if not isinstance(frames, list) or not frames:
        raise HTTPException(
            status_code=400,
            detail="저장할 프레임 데이터가 없습니다.",
        )

    output_path = OUTPUT_DIR / JSON_FILENAME

    output_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "saved": True,
        "file": JSON_FILENAME,
        "path": f"output/{JSON_FILENAME}",
        "frame_count": len(frames),
    }