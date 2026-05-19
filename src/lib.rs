use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};

#[pyfunction]
fn remove_empty(obj: Py<PyAny>, py: Python) -> PyResult<Py<PyAny>> {
    let obj_ref = obj.bind(py);

    if let Ok(dict) = obj_ref.clone().cast::<PyDict>() {
        let result = PyDict::new(py);
        for (key, value) in dict.iter() {
            let cleaned = remove_empty(value.into(), py)?;
            let cleaned_ref = cleaned.bind(py);

            let should_keep = if let Ok(list) = cleaned_ref.clone().cast::<PyList>() {
                !list.is_empty()
            } else if let Ok(d) = cleaned_ref.clone().cast::<PyDict>() {
                !d.is_empty()
            } else {
                !cleaned_ref.is_none()
            };

            if should_keep {
                result.set_item(key, cleaned)?;
            }
        }
        Ok(result.into())
    } else if let Ok(list) = obj_ref.clone().cast::<PyList>() {
        let result = PyList::empty(py);
        for item in list.iter() {
            let cleaned = remove_empty(item.into(), py)?;
            let cleaned_ref = cleaned.bind(py);

            let should_keep = if let Ok(l) = cleaned_ref.clone().cast::<PyList>() {
                !l.is_empty()
            } else if let Ok(d) = cleaned_ref.clone().cast::<PyDict>() {
                !d.is_empty()
            } else {
                !cleaned_ref.is_none()
            };

            if should_keep {
                result.append(cleaned)?;
            }
        }
        Ok(result.into())
    } else {
        Ok(obj)
    }
}

#[pymodule]
fn mashumaronone(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(remove_empty, m)?)?;
    Ok(())
}
