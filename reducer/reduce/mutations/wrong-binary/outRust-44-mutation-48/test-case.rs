use std::collections::hash_map::DefaultHasher;
use std::env;
use std::hash::{Hash, Hasher};
macro_rules! c {
    ($a:expr,$b:expr, $d: expr) => {{
        let denominator = $b;
        if denominator != $d {
            $a
        } else {
            $d
        }
    }};
}
#[derive(Debug)]
struct e {
    t: f32,
    f: f32,
}
struct g {
    h: u16,
}
struct i {
    j: g,
    k: i128,
    l: i32,
}
impl i {
    fn m(self, n: usize, o: u32, hasher: &DefaultHasher) -> f32 {
        0.5911941f32
    }
}
fn main() {
    let p: Vec<String> = env::args().collect();
    let mut q = DefaultHasher::new();
    let hasher = &mut q;
    let r = e {
        t: p[6].parse().unwrap(),
        f: c!(
            0.6719413f32,
            i {
                j: g { h: 6 },
                k: p[13].parse().unwrap(),
                l: 0
            }
            .m([2].len(), 2, hasher),
            0.0f32
        ),
    };
    let s = r;
    format!("{:?}", s).hash(hasher);
    println!("{}", hasher.finish())
}
