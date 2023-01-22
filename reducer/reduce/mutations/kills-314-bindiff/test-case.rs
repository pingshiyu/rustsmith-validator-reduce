use std::env;
fn main() {
    let a: Vec<String> = env::args().collect();
    let b = a[2].parse().unwrap();
    let c = b;
    let h = a[1].parse().unwrap();
    let d = h;
    let e = d;
    let i: Option<i8> = if e { None } else { Some(a[3].parse().unwrap()) };
    let _f: (Option<String>, u32, u16) = (
        Some(c),
        match i {
            None => 2,
            _g => a[9].parse().unwrap(),
        },
        a[4].parse().unwrap(),
    );
}
