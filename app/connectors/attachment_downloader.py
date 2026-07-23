from pathlib import Path

import httpx

from app.config.settings import settings
from app.utils.logger import logger


class AttachmentDownloader:

    def __init__(self):

        self.base_url = settings.CONFLUENCE_URL.rstrip("/")

        self.auth = (
            settings.USERNAME,
            settings.PASSWORD
        )

        self.download_dir = Path("downloads")

        self.download_dir.mkdir(
            exist_ok=True
        )

    def download(
        self,
        attachment
    ):

        if not attachment.download_url:

            logger.warning(
                f"No download URL for {attachment.filename}"
            )

            return None


        url = (
            self.base_url +
            attachment.download_url
        )


        file_path = (
            self.download_dir /
            attachment.filename
        )


        logger.info(
            f"Downloading {attachment.filename}"
        )


        with httpx.stream(

            "GET",

            url,

            auth=self.auth,

            timeout=120

        ) as response:

            response.raise_for_status()

            with open(
                file_path,
                "wb"
            ) as f:

                for chunk in response.iter_bytes():

                    f.write(chunk)


        logger.info(
            f"Saved to {file_path}"
        )

        return file_path