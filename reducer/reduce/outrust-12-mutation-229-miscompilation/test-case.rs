use std::env;
struct a {
  b : u64, c : String, d : usize, e : i8
} fn main() {
  let f : Vec<String> = env::args().collect();
  a {
  b:
    f[1].parse().unwrap(), c : if f[6].parse().unwrap() { String::from("") }
    else {String::from("")}, d : f[5].parse().unwrap(),
        e : f[5].clone().parse().unwrap()
  };
}
