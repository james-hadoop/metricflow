from __future__ import annotations

from typing import List, Optional, Sequence

from metricflow.model.objects.common import Element, Metadata
from metricflow.model.objects.elements.dimension import Dimension
from metricflow.model.objects.elements.identifier import Identifier
from metricflow.model.objects.elements.measure import Measure
from metricflow.model.objects.utils import ParseableObject, HashableBaseModel
from metricflow.object_utils import ExtendedEnum
from metricflow.specs import LinkableElementReference, MeasureReference


class DataSourceOrigin(ExtendedEnum):
    """Describes how data sources were created

    Impacts determination of validity and duration of storage
    """

    SOURCE = "source"  # "input" data sources
    DERIVED = "derived"  # generated by the semantic layer originating (perhaps indirectly) from sources


class MutabilityType(ExtendedEnum):
    """How data at the physical layer is expected to behave"""

    UNKNOWN = "UNKNOWN"
    IMMUTABLE = "IMMUTABLE"  # never changes
    APPEND_ONLY = "APPEND_ONLY"  # appends along an orderable column
    DS_APPEND_ONLY = "DS_APPEND_ONLY"  # appends along daily column
    FULL_MUTATION = "FULL_MUTATION"  # no guarantees, everything may change


class MutabilityTypeParams(HashableBaseModel, ParseableObject):
    """Type params add additional context to mutability"""

    min: Optional[str]
    max: Optional[str]
    update_cron: Optional[str]
    along: Optional[str]


class Mutability(HashableBaseModel, ParseableObject):
    """Describes the mutability properties of a data source"""

    type: MutabilityType
    type_params: Optional[MutabilityTypeParams]


class DataSource(HashableBaseModel, ParseableObject):
    """Describes a data source"""

    name: str
    description: Optional[str]
    sql_table: Optional[str]
    sql_query: Optional[str]
    dbt_model: Optional[str]

    identifiers: Sequence[Identifier] = []
    measures: Sequence[Measure] = []
    dimensions: Sequence[Dimension] = []

    mutability: Mutability

    origin: DataSourceOrigin = DataSourceOrigin.SOURCE
    metadata: Optional[Metadata]

    @property
    def elements(self) -> List[Element]:  # noqa: D
        res: List[Element] = []
        res.extend(self.identifiers)
        res.extend(self.dimensions)

        return res

    @property
    def element_names(self) -> List[LinkableElementReference]:  # noqa: D
        return [n.name for n in self.elements]

    @property
    def identifier_names(self) -> List[LinkableElementReference]:  # noqa: D
        return [i.name for i in self.identifiers]

    @property
    def dimension_names(self) -> List[LinkableElementReference]:  # noqa: D
        return [i.name for i in self.dimensions]

    @property
    def measure_names(self) -> List[MeasureReference]:  # noqa: D
        return [i.name for i in self.measures]

    def get_measure(self, measure_name: MeasureReference) -> Measure:  # noqa: D
        for measure in self.measures:
            if measure.name == measure_name:
                return measure

        raise ValueError(f"No dimension with name ({measure_name}) in data source with name ({self.name})")

    def get_element(self, name: LinkableElementReference) -> Element:  # noqa: D
        for dim in self.dimensions:
            if dim.name == name:
                return dim
        for ident in self.identifiers:
            if ident.name == name:
                return ident

        raise ValueError(f"No dimension with name ({name}) in data source with name ({self.name})")

    def get_dimension(self, dimension_name: LinkableElementReference) -> Dimension:  # noqa: D
        for dim in self.dimensions:
            if dim.name == dimension_name:
                return dim

        raise ValueError(f"No dimension with name ({dimension_name}) in data source with name ({self.name})")

    def get_identifier(self, identifier_name: LinkableElementReference) -> Identifier:  # noqa: D
        for ident in self.identifiers:
            if ident.name == identifier_name:
                return ident

        raise ValueError(f"No identifier with name ({identifier_name}) in data source with name ({self.name})")

    @property
    def partitions(self) -> List[Dimension]:  # noqa: D
        return [dim for dim in self.dimensions or [] if dim.is_partition]

    @property
    def partition(self) -> Optional[Dimension]:  # noqa: D
        partitions = self.partitions
        if not partitions:
            return None
        if len(partitions) > 1:
            raise ValueError(f"too many partitions for data source {self.name}")
        return partitions[0]
