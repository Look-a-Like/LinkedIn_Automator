# app/routes/proxy.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

router = APIRouter(
    prefix="/proxy",
    tags=["proxy"]
)

FIVETRAN_WEBHOOK_URL = "https://webhooks.fivetran.com/webhooks/615b5e5c-9fde-4c75-a034-f642dba74c1f"

@router.post("/fivetran")
async def proxy_to_fivetran(request: Request):
    try:
        payload = await request.body()
        headers = {
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                FIVETRAN_WEBHOOK_URL,
                headers=headers,
                content=payload
            )

        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy Error: {str(e)}")
