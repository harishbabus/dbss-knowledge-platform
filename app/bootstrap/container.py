from __future__ import annotations
from app.config.settings import settings

from app.builders.knowledge_builder import KnowledgeBuilder


from app.crawler.inventory import KnowledgeCrawler
from app.crawler.delta_sync import DeltaSyncCrawler
from app.services.chunk_service import ChunkService
from app.connectors.attachment_downloader import AttachmentDownloader

from app.services.page_processor import PageProcessor
from app.storage.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)
from app.extractors.attachment_extractor import AttachmentExtractor
from app.extractors.attachment_content_extractor import (
    AttachmentContentExtractor,
)

from app.indexing.chunk_stage import ChunkStage
from app.indexing.persist_stage import PersistStage
from app.indexing.pipeline import IndexingPipeline
from app.extractors.page_extractor import PageExtractor

from app.repositories.attachment_content_repository import (
    AttachmentContentRepository,
)
from app.repositories.sync_checkpoint_repository import (
    SyncCheckpointRepository,
)
from app.storage.attachment_repository import AttachmentRepository
from app.storage.knowledge_repository import KnowledgeRepository
from app.services.attachment_processor import AttachmentProcessor
from app.chunking.splitter_factory import SplitterFactory


class Container:
    """
    Composition Root for the application.

    Responsible for creating and wiring
    application services.
    """

    def __init__(self):
        #
        # Builder
        #
        self.knowledge_builder = KnowledgeBuilder()

        #
        # Chunking
        #
        self.splitter = SplitterFactory.create(settings.CHUNK_SPLITTER)

        self.chunk_service = ChunkService(self.splitter)

        #
        # Chunk Storage
        #
        self.chunk_repository = KnowledgeChunkRepository()

        #
        # Indexing Pipeline
        #
        self.indexing_pipeline = IndexingPipeline(
            [
                ChunkStage(self.chunk_service),
                PersistStage(self.chunk_repository),
            ]
        )

        #
        # Page Extraction
        #
        self.page_extractor = PageExtractor()

        #
        # Attachment Download
        #
        self.attachment_downloader = AttachmentDownloader()

        #
        # Attachment Content Extraction
        #
        self.attachment_content_extractor = AttachmentContentExtractor()

        #
        # Attachment Extraction
        #
        self.attachment_extractor = AttachmentExtractor()

        #
        # Repositories
        #
        self.knowledge_repository = KnowledgeRepository()

        self.attachment_repository = AttachmentRepository()

        self.attachment_content_repository = AttachmentContentRepository()

        self.sync_checkpoint_repository = SyncCheckpointRepository()

        self.attachment_processor = AttachmentProcessor(
            attachment_repo=self.attachment_repository,
            content_repo=self.attachment_content_repository,
            downloader=self.attachment_downloader,
            content_extractor=self.attachment_content_extractor,
        )

        #
        # Page Processor
        #
        self.page_processor = PageProcessor(
            indexing_pipeline=self.indexing_pipeline,
            builder=self.knowledge_builder,
            page_extractor=self.page_extractor,
            attachment_extractor=self.attachment_extractor,
            knowledge_repo=self.knowledge_repository,
            attachment_repo=self.attachment_repository,
            attachment_processor=self.attachment_processor,
        )

        #
        # Full Inventory Crawler
        #
        self.crawler = KnowledgeCrawler(
            page_processor=self.page_processor,
            checkpoint_repository=self.sync_checkpoint_repository,
        )

        #
        # Delta sync crawler
        #
        self.delta_sync_crawler = DeltaSyncCrawler(
            page_processor=self.page_processor,
            checkpoint_repository=self.sync_checkpoint_repository,
        )
