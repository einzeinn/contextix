"""Tech stack detection — finds languages, frameworks, databases, and infrastructure."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument


class TechStackDetector:
    """Detect the technology stack from dependency manifests and documentation.

    Strategies:
    1. File-type inference: detect languages from document file types
    2. Dependency manifest parsing: pyproject.toml, requirements.txt, package.json
    3. Infrastructure detection: Docker, Kubernetes, CI configs
    4. Database detection: specific database references in docs
    """

    KNOWN_DATABASES = [
        re.compile(r"\bPostgreSQL\b", re.IGNORECASE),
        re.compile(r"\bMySQL\b", re.IGNORECASE),
        re.compile(r"\bSQLite\b", re.IGNORECASE),
        re.compile(r"\bMongoDB\b", re.IGNORECASE),
        re.compile(r"\bRedis\b", re.IGNORECASE),
        re.compile(r"\bDynamoDB\b", re.IGNORECASE),
        re.compile(r"\bCassandra\b", re.IGNORECASE),
        re.compile(r"\bElasticsearch\b", re.IGNORECASE),
        re.compile(r"\bCouchDB\b", re.IGNORECASE),
        re.compile(r"\bFirebase\b", re.IGNORECASE),
        re.compile(r"\bSupabase\b", re.IGNORECASE),
        re.compile(r"\bNeo4j\b", re.IGNORECASE),
        re.compile(r"\bClickHouse\b", re.IGNORECASE),
        re.compile(r"\bBigQuery\b", re.IGNORECASE),
        re.compile(r"\bSnowflake\b", re.IGNORECASE),
    ]

    KNOWN_INFRASTRUCTURE = [
        re.compile(r"\bDocker\b", re.IGNORECASE),
        re.compile(r"\bKubernetes\b", re.IGNORECASE),
        re.compile(r"\bAWS\b"),
        re.compile(r"\b(?:Google\s+Cloud|GCP)\b", re.IGNORECASE),
        re.compile(r"\bAzure\b", re.IGNORECASE),
        re.compile(r"\bTerraform\b", re.IGNORECASE),
        re.compile(r"\bAnsible\b", re.IGNORECASE),
        re.compile(r"\bGitHub\s+Actions\b", re.IGNORECASE),
        re.compile(r"\bGitLab\s+CI\b", re.IGNORECASE),
        re.compile(r"\bJenkins\b", re.IGNORECASE),
        re.compile(r"\bNginx\b", re.IGNORECASE),
        re.compile(r"\bCloudflare\b", re.IGNORECASE),
        re.compile(r"\bVercel\b", re.IGNORECASE),
        re.compile(r"\bNetlify\b", re.IGNORECASE),
        re.compile(r"\bHeroku\b", re.IGNORECASE),
        re.compile(r"\bFly\.io\b", re.IGNORECASE),
        re.compile(r"\bRailway\b", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        stack: set[str] = set()

        stack.update(self._file_type_languages(documents))
        stack.update(self._dependency_names(documents))
        stack.update(self._detect_databases(documents))
        stack.update(self._detect_infrastructure(documents))

        return sorted(stack)

    def _file_type_languages(self, documents: list[ParsedDocument]) -> set[str]:
        types = {doc.file_type for doc in documents}
        mapping = {
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "rust": "Rust",
            "go": "Go",
            "java": "Java",
            "kotlin": "Kotlin",
            "swift": "Swift",
            "ruby": "Ruby",
            "php": "PHP",
            "c": "C",
            "cpp": "C++",
            "csharp": "C#",
            "scala": "Scala",
            "elixir": "Elixir",
            "haskell": "Haskell",
            "clojure": "Clojure",
            "lua": "Lua",
            "zig": "Zig",
            "dart": "Dart",
        }
        return {mapping[t] for t in types if t in mapping}

    def _dependency_names(self, documents: list[ParsedDocument]) -> set[str]:
        names: set[str] = set()

        pyproject = self._find_doc(documents, "pyproject.toml")
        if pyproject:
            for line in pyproject.content.splitlines():
                match = re.match(r'^\s*"([A-Za-z0-9_.-]+)\s*[><=~!]', line.strip())
                if match:
                    names.add(match.group(1))

        requirements = self._find_doc(documents, "requirements.txt")
        if requirements:
            for line in requirements.content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                match = re.match(r"^([A-Za-z0-9_.-]+)", stripped)
                if match:
                    names.add(match.group(1))

        package_json = self._find_doc(documents, "package.json")
        if package_json:
            exclude = {
                "name", "version", "scripts", "dependencies", "devDependencies",
                "main", "license", "description", "type", "private", "author",
                "keywords", "repository", "bugs", "homepage", "engines",
                "exports", "files", "bin", "directories", "funding",
            }
            for match in re.finditer(r'"([A-Za-z0-9@/_.-]+)"\s*:\s*"[^"]*"', package_json.content):
                name = match.group(1)
                if name not in exclude:
                    names.add(name)

        return names

    def _detect_databases(self, documents: list[ParsedDocument]) -> set[str]:
        found: set[str] = set()
        for doc in documents:
            for pat in self.KNOWN_DATABASES:
                match = pat.search(doc.content)
                if match:
                    found.add(match.group(0))
        return found

    def _detect_infrastructure(self, documents: list[ParsedDocument]) -> set[str]:
        found: set[str] = set()
        for doc in documents:
            for pat in self.KNOWN_INFRASTRUCTURE:
                match = pat.search(doc.content)
                if match:
                    found.add(match.group(0))
        return found

    def _find_doc(self, documents: list[ParsedDocument], source: str) -> ParsedDocument | None:
        return next((d for d in documents if d.source.lower() == source.lower()), None)