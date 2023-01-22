use std::collections::hash_map::DefaultHasher;
use std::env;
fn a(b: i32, c: &DefaultHasher) -> u8 {
    match Some(String::from("")) {
        None => String::from(""),
        Some(d) => String::from(""),
    };
    8
}
fn main() {
    let e: Vec<String> = env::args().collect();
    let f = DefaultHasher::new();
    let c = &f;
    a(e[1].parse().unwrap(), c);
}
