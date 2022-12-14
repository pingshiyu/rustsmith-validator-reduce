use std::env;
struct a {
  b : u8, c : Option<u8>
} 

fn main() {
  let d : Vec<String> = env::args().collect();
  {}
  a{b : d[4].parse().unwrap(), c : Some(8)};
}
