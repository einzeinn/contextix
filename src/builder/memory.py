"""Build ProjectMemory from Context IR."""

from contextix.models import ContextIR, ProjectMemory


class MemoryBuilder:
    """Convert internal analysis into persistent project memory."""

    def build(self, context: ContextIR) -> ProjectMemory:
        return ProjectMemory(**context.__dict__)
