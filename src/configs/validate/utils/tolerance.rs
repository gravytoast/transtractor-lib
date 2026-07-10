/// General validator for tolerance values.
pub fn validate_tolerance(val: i32) -> Result<(), String> {
    if val < 0 {
        return Err("Must be >= 0".to_string());
    }
    Ok(())
}
