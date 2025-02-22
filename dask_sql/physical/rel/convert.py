import logging
from typing import TYPE_CHECKING

import dask.dataframe as dd

from dask_sql.java import get_java_class
from dask_sql.physical.rel.base import BaseRelPlugin
from dask_sql.utils import LoggableDataFrame, Pluggable

if TYPE_CHECKING:
    import dask_sql
    from dask_sql.java import org

logger = logging.getLogger(__name__)


class RelConverter(Pluggable):
    """
    Helper to convert from rel to a python expression

    This class stores plugins which can convert from RelNodes to
    python expression (typically dask dataframes).
    The stored plugins are assumed to have a class attribute "class_name"
    to control, which java classes they can convert
    and they are expected to have a convert (instance) method
    in the form

        def convert(self, rel, context)

    to do the actual conversion.
    """

    @classmethod
    def add_plugin_class(cls, plugin_class: BaseRelPlugin, replace=True):
        """Convenience function to add a class directly to the plugins"""
        logger.debug(f"Registering REL plugin for {plugin_class.class_name}")
        cls.add_plugin(plugin_class.class_name, plugin_class(), replace=replace)

    @classmethod
    def convert(
        cls, rel: "org.apache.calcite.rel.RelNode", context: "dask_sql.Context"
    ) -> dd.DataFrame:
        """
        Convert the given rel (java instance)
        into a python expression (a dask dataframe)
        using the stored plugins and the dictionary of
        registered dask tables from the context.
        """
        class_name = get_java_class(rel)

        try:
            plugin_instance = cls.get_plugin(class_name)
        except KeyError:  # pragma: no cover
            raise NotImplementedError(
                f"No conversion for class {class_name} available (yet)."
            )
        logger.debug(
            f"Processing REL {rel} using {plugin_instance.__class__.__name__}..."
        )
        df = plugin_instance.convert(rel, context=context)
        logger.debug(f"Processed REL {rel} into {LoggableDataFrame(df)}")
        return df
