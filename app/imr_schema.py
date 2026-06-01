from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class Property(BaseModel):
    """A single property/filter on an entity."""

    name: str = Field(
        description="Property key, e.g. 'brand', 'cuisine', 'height', 'outdoor seating'"
    )
    operator: Optional[Literal["=", "~", ">", "<"]] = Field(
        default=None, description="Comparison operator. Omit for boolean properties."
    )
    value: Optional[str] = Field(
        default=None, description="Property value. Omit for boolean properties."
    )


class Entity(BaseModel):
    """A geographic entity extracted from the sentence."""

    id: int = Field(description="Integer id starting at 0")
    type: Literal["nwr", "cluster"] = Field(
        description="'nwr' for single entities or unquantified plurals. 'cluster' only when a specific count or vague group quantifier is given."
    )
    name: str = Field(
        description="Generic entity type name, never a brand. May use 'brand:<Name>' prefix for pure brand queries."
    )
    minPoints: Optional[int] = Field(
        default=None, description="Cluster only: minimum number of members."
    )
    maxDistance: Optional[str] = Field(
        default=None,
        description="Cluster only: maximum spread between members, e.g. '50 m', '1.2 km'.",
    )

    properties: Optional[list[Property]] = Field(
        default=None, description="Optional list of property filters. Omit if none."
    )

    @model_validator(mode="after")
    def clear_cluster_fields_for_nwr(self) -> "Entity":
        """Strip cluster-only fields when type is 'nwr'."""
        if self.type == "nwr":
            self.minPoints = None
            self.maxDistance = None
        return self


class Area(BaseModel):
    """The geographic area of the query."""

    type: Literal["area", "bbox"] = Field(
        description="'area' if a named place is mentioned, 'bbox' otherwise."
    )
    value: Optional[str] = Field(
        default=None,
        description="Canonical place name. Only present when type is 'area'.",
    )


class Relation(BaseModel):
    """A spatial relation between two entities."""

    source: int = Field(description="Id of the source entity.")
    target: int = Field(description="Id of the target entity.")
    type: Literal["distance", "contains"] = Field(
        description="'distance' for proximity, 'contains' when one entity is inside another."
    )
    value: Optional[str] = Field(
        default=None,
        description="Distance as a string with units, e.g. '400 m', '1.2 km'. Only for 'distance' type.",
    )
    spatial_term: Optional[str] = Field(
        default=None,
        description="Descriptive spatial phrase if the user used one, e.g. 'next to', 'close to'. Only for 'distance' type.",
    )


class IMROutput(BaseModel):
    """Full structured output of the IMR extraction."""

    area: Area
    entities: list[Entity] = Field(description="List of geographic entities.")
    relations: Optional[list[Relation]] = Field(
        default=None, description="Optional list of spatial relations between entities."
    )

    def to_yaml(self) -> str:
        """Serialize the IMROutput to a clean YAML string (None fields excluded)."""
        return yaml.dump(
            self.model_dump(exclude_none=True),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
