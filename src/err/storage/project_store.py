from pathlib import Path

import frontmatter

from err.models.project import ProjectDoc, ProjectFrontmatter


class ProjectStore:
    @staticmethod
    def load(path: Path, theme_slug: str, parent_slug: str | None = None) -> ProjectDoc:
        """Parse project.md into a ProjectDoc."""
        post = frontmatter.load(str(path))
        fm = ProjectFrontmatter.model_validate(dict(post.metadata))
        return ProjectDoc(
            frontmatter=fm,
            body=post.content,
            path=path,
            theme_slug=theme_slug,
            parent_slug=parent_slug,
        )

    @staticmethod
    def save(doc: ProjectDoc) -> None:
        """Serialize ProjectDoc back to YAML frontmatter + Markdown body."""
        metadata = doc.frontmatter.model_dump()
        post = frontmatter.Post(content=doc.body, **metadata)
        doc.path.write_text(frontmatter.dumps(post), encoding="utf-8")
