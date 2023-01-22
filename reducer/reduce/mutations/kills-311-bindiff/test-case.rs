use std::collections::hash_map::DefaultHasher;
use std::env;
struct b {
    c: u32,
    d: usize,
    e: u32,
    p: String,
}
struct f {
    g: Box<i32>,
    h: Vec<i128>,
}
struct i {
    j: f32,
    k: bool,
    l: i64,
}
impl i {
    fn m(self, n: Box<i32>, o: Box<i8>, a: &DefaultHasher) -> i128 {
        8
    }
}
fn q(a: &DefaultHasher) -> usize {
    1680594027571012646usize
}
fn r(f: u128, b: i8, a: &DefaultHasher) -> bool {
    let ab = false;
    ab
}
fn ac(e: &String, f: bool, ad: Option<f64>, a: &DefaultHasher) -> u128 {
    8
}
fn ae(af: i32, aa: &DefaultHasher) {
    let ag = 5;
    let ah = 0;
    let t = 0;
    let u = t;
    let ai = 2;
    let aj = 2;
    let v = String::from("");
    let w = v;
    let x = b {
        c: ai,
        d: q(aa),
        e: aj,
        p: w,
    };
    let y = x;
    let ak = Box::new(9);
    let al = ak;
    let am = f { g: al, h: vec![] };
    let an = Box::new(4);
    let ao = an;
    let ap = ao;
    let z = ap;
    let aq = f {
        g: Box::new(0),
        h: vec![i {
            j: 0.079640985f32,
            k: true,
            l: 6,
        }
        .m(Box::new(u), z, aa)],
    };
    let ar = true;
    let var263 = ar;
    let var434 = &y.p;
    let var315 = ac(var434, var263, None, aa);
    let var314 = var315;
    let var313 = var314;
    let var312 = var313;
    let var311 = var312;
    let var435 = Box::new(ag);
    let var262 = vec![i {
        j: 0.61452526f32,
        k: r(var311, ah, aa),
        l: 7,
    }
    .m(var435, Box::new(8), aa)];
    let var438 = Some(ah);
    let var437 = var438;
    let var436 = match var437 {
        None => {
            let var509 = vec![];
            var509
        }
        Some0 => return,
    };
    [
        am,
        aq,
        f {
            g: Box::new(ag),
            h: var262,
        },
        f {
            g: Box::new(u),
            h: var436,
        },
    ];
    match None::<Vec<i64>> {
        None => return,
        Some0 => f {
            g: Box::new(5),
            h: vec![],
        },
    };
}
fn main() {
    let cli_args: Vec<String> = env::args().collect();
    let s = DefaultHasher::new();
    let aa = &s;
    let var870 = 7;
    let var866 = var870;
    let var865 = var866;
    ae(var865, aa);
    let var3477 = cli_args[7].parse().unwrap();
    let var3476 = var3477;
    vec![].push(f {
        g: Box::new(cli_args[1].parse().unwrap()),
        h: if var3476 { vec![] } else { vec![] },
    })
}
