use std::collections::hash_map::DefaultHasher;
use std::env;
use std::hash::{Hash, Hasher};
const a: u128 = 8;
struct b {
    c: String,
    d: Vec<u8>,
    e: usize,
    f: u128,
}
fn main() {
    let g: Vec<String> = env::args().collect();
    let mut h = DefaultHasher::new();
    let hasher = &mut h;
    let aa = g[7].parse().unwrap();
    let ab = Some(a);
    let i = vec![];
    let ac = i;
    let j = ac;
    let k = j;
    let l: Option<(b, i64, usize, Option<u128>)> = Some((
        b {
            c: g[0].parse().unwrap(),
            d: k,
            e: g[1].parse().unwrap(),
            f: g[5].parse().unwrap(),
        },
        aa,
        14203710862295110329usize,
        ab,
    ));
    let m: ((i128, i128, f64, Box<bool>), Box<Box<u8>>, f32) = (
        (
            6,
            7,
            g[3].parse().unwrap(),
            Box::new(g[12].parse().unwrap()),
        ),
        {
            match 0 {
                n => {
                    let mut ad = (2,);
                    ad.0 = 32;
                    ad.hash(hasher)
                }
            }
            Box::new(Box::new(g[2].parse().unwrap()))
        },
        g[6].parse().unwrap(),
    );
    println!("{}", hasher.finish())
}
