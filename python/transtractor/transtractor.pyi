"""Stub file for transtractor Rust extension module."""

class LibParser:
    """Parser for extracting statement data from text items."""

    def __init__(self) -> None:
        """Create a new LibParser instance."""

    def register_config_from_json_str(self, py_json_str: str) -> None:
        """
        Register JSON configuration string into the parser database.

        :param py_json_str: JSON string containing the configuration
        :type py_json_str: str
        :raises ConfigLoadError: If the configuration cannot be loaded
        """

    def register_config_from_file(self, py_file_path: str) -> None:
        """
        Register JSON configuration file into the parser database.

        :param py_file_path: Path to the JSON configuration file
        :type py_file_path: str
        :raises ConfigLoadError: If the configuration file cannot be loaded
        """

    def py_text_items_to_py_statement_data(self, py_text_items: list[dict]) -> object:
        """
        Process a Python list of text items and return statement data.

        :param py_text_items: List of text item dictionaries
        :type py_text_items: list[dict]
        :returns: StatementData object
        :rtype: object
        :raises StatementNotSupported: If no supported statement configuration is found
        :raises NoErrorFreeStatementData: If no error-free statement data could be found
        """

    def py_text_items_to_debug_py_str(self, py_text_items: list[dict]) -> str:
        """
        Process a Python list of text items and return debug information as a string.

        :param py_text_items: List of text item dictionaries
        :type py_text_items: list[dict]
        :returns: Debug information string
        :rtype: str
        """

    def py_text_items_to_layout_py_str(
        self, py_text_items: list[dict], y_bin: float, x_gap: float
    ) -> str:
        """
        Process a Python list of text items and return layout text as a string.

        :param py_text_items: List of text item dictionaries
        :type py_text_items: list[dict]
        :param y_bin: Y coordinate bin size for sorting/merging text items
        :type y_bin: float
        :param x_gap: X coordinate gap size for merging text items
        :type x_gap: float
        :returns: Layout text string
        :rtype: str
        """

    def py_layout_py_str_to_py_text_items(self, layout_str: str) -> list[dict]:
        """
        Process a layout text string and return a Python list of text item dictionaries.

        :param layout_str: Layout text string
        :type layout_str: str
        :returns: List of text item dictionaries
        :rtype: list[dict]
        """

class NoErrorFreeStatementData(Exception):
    """Raised when no error-free statement data could be found."""

class ConfigLoadError(Exception):
    """Raised when a configuration cannot be loaded."""

class StatementNotSupported(Exception):
    """Raised when no supported statement configuration is found."""
