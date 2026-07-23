from datetime import datetime, timezone

from app.repositories.sync_checkpoint_repository import (
    SyncCheckpointRepository
)

from app.models.sync_checkpoint import (
    SyncCheckpoint
)


repo = SyncCheckpointRepository()



#
# Create / update checkpoint
#
checkpoint = SyncCheckpoint(

    id="DPCC",

    last_sync_time=datetime.now(
        timezone.utc
    ),

    status="SUCCESS"

)


repo.save(
    checkpoint
)



#
# Read checkpoint
#
result = (
    repo.get(
        "DPCC"
    )
)


print(
    "Checkpoint:"
)

print(
    result
)