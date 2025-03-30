import os
import uuid
from io import BytesIO
import requests
from fastapi import FastAPI, HTTPException
from azure.storage.blob import BlobServiceClient
from PIL import Image
from rembg import remove

app = FastAPI()

# Azure Configuration
AZURE_CONN_STR = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = "bg-removed-images"
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


@app.post("/remove-bg/")
async def remove_background(image_url: str):
    try:
        response = requests.get(image_url)
        response.raise_for_status()

        input_image = Image.open(BytesIO(response.content))

        input_image_bytes = BytesIO()
        input_image.save(input_image_bytes, format="PNG")
        input_image_bytes.seek(0)

        output_image_bytes = remove(input_image_bytes.getvalue())
        processed_image = Image.open(BytesIO(output_image_bytes))

        buffer = BytesIO()
        processed_image.save(buffer, format="PNG")
        buffer.seek(0)

        blob_name = f"{uuid.uuid4()}.png"  # Generate a unique name for the file
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(buffer.read(), overwrite=True, content_type="image/png")

        processed_image_url = f"https://{blob_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}"

        return {"processed_image_url": processed_image_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
