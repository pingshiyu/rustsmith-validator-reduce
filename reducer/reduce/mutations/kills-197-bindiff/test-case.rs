use std::collections::hash_map::DefaultHasher;
use std::hash::Hash;
fn main() {
  let mut a = DefaultHasher::new ();
  let b = &mut a;
  "".hash(b)
}
