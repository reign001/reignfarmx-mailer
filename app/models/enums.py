from enum import Enum


class EmailStatus(Enum):

    PENDING = "Pending"

    PROCESSING = "Processing"

    SENT = "Sent"

    FAILED = "Failed"

    OPENED = "Opened"

    REPLIED = "Replied"