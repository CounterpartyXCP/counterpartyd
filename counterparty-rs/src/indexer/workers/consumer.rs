use crossbeam_channel::{select, Receiver, Sender};

use crate::indexer::types::{error::Error, pipeline::Done};

pub fn new<U, V>() -> impl Fn(Receiver<U>, Sender<V>, Done) -> Result<(), Error> + Clone {
    move |rx, _, done| loop {
        select! {
          recv(done) -> _ => return Ok(()),
          recv(rx) -> result => {
              if result.is_err() {
                  return Ok(())
              }
          }
        }
    }
}
