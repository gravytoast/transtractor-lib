use crate::configs::db::ConfigDB;
use crate::parsers::flows::layout_to_text_items::layout_to_text_items;
use crate::parsers::flows::text_items_to_debug::text_items_to_debug;
use crate::parsers::flows::text_items_to_layout::text_items_to_layout;
use crate::parsers::flows::text_items_to_statement_datas::text_items_to_statement_datas;
use crate::python::exceptions::{ConfigLoadError, NoErrorFreeStatementData, StatementNotSupported};
use crate::python::utils;
use pyo3::prelude::*;

#[pyclass]
#[derive(Default)]
pub struct LibParser {
    db: ConfigDB,
}

#[pymethods]
impl LibParser {
    /// Create a new Parser instance
    #[new]
    pub fn new() -> Self {
        Self {
            db: ConfigDB::new(),
        }
    }

    /// Register JSON configuration string into the parser database
    pub fn register_config_from_json_str(&mut self, py_json_str: &str) -> PyResult<()> {
        match self.db.register_from_str(py_json_str) {
            Ok(_) => Ok(()),
            Err(e) => Err(ConfigLoadError::new_err(e)),
        }
    }

    /// Import JSON configuration file into the parser database and update the StatementTyper.
    pub fn register_config_from_file(&mut self, py_file_path: &str) -> PyResult<()> {
        match self.db.register_from_file(py_file_path) {
            Ok(_) => {}
            Err(e) => return Err(ConfigLoadError::new_err(e)),
        }
        Ok(())
    }

    /// Process a Python list of text items and return statement data as a
    /// Python object of type StatementData.
    pub fn py_text_items_to_py_statement_data(
        &self,
        py_text_items: &Bound<'_, pyo3::types::PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let text_items = utils::py_text_items_to_rust_text_items(py_text_items)?;
        let configs = self.db.identify(&text_items);
        if configs.is_empty() {
            return Err(StatementNotSupported::new_err(
                "No supported statement configuration found for the provided text items.",
            ));
        }

        let statement_data_results = text_items_to_statement_datas(&text_items, &configs)
            .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;

        // Return the first error-free StatementData
        for data in statement_data_results {
            if data.errors.is_empty() {
                return utils::rust_statement_data_to_py_statement_data(&data);
            }
        }

        // Package error if statement is identified for not parseable
        let applicable_config_keys: Vec<String> =
            configs.iter().map(|cfg| cfg.key.clone()).collect();
        Err(NoErrorFreeStatementData::new_err(format!(
            "No error-free StatementData found. This indicates an error in one of the configurations: {}. See further details using the \"debug\" method. Please contact a developer if this config is part of the default set provided by the package.",
            applicable_config_keys.join(", ")
        )))
    }

    /// Process a Python list of text items and return debug information as a string.
    pub fn py_text_items_to_debug_py_str(
        &self,
        py_text_items: &Bound<'_, pyo3::types::PyAny>,
    ) -> PyResult<String> {
        let text_items = utils::py_text_items_to_rust_text_items(py_text_items)?;
        let configs = self.db.identify(&text_items);
        if configs.is_empty() {
            return Err(StatementNotSupported::new_err(
                "No supported statement configuration found for the provided text items.",
            ));
        }

        match text_items_to_debug(&text_items, &configs) {
            Ok(debug_str) => Ok(debug_str),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
        }
    }

    /// Process a Python list of text items and return layout text as a string.
    pub fn py_text_items_to_layout_py_str(
        &self,
        py_text_items: &Bound<'_, pyo3::types::PyAny>,
        y_bin: f32,
        x_gap: f32,
    ) -> PyResult<String> {
        let text_items = utils::py_text_items_to_rust_text_items(py_text_items)?;
        match text_items_to_layout(&text_items, y_bin, x_gap) {
            Ok(layout_str) => Ok(layout_str),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
        }
    }

    /// Process a Python layout text string and return a Python list of text item dictionaries.
    pub fn py_layout_py_str_to_py_text_items(
        &self,
        py_layout_str: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let rust_layout_str = py_layout_str.extract::<String>()?;
        let text_items = layout_to_text_items(&rust_layout_str).map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!(
                "Failed to convert layout string to text items: {}",
                e
            ))
        })?;
        utils::rust_text_items_to_py_text_items(&text_items)
    }
}
