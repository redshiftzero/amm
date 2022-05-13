use ark_bls12_377::Fq;
use ark_ff::{Field, UniformRand, Zero};
use rand_core::RngCore;

/// Represents the `RawData` we want to encode.
pub struct RawData(pub Vec<u8>);

/// Represents an Reed-Solomon encoding of the `RawData`.
impl RawData {
    /// Get the Reed-Solomon encoding evaluated at a `ChallengeElement`
    pub fn reed_solomon_encoding(&self, r: &ChallengeElement) -> Evaluation {
        let mut v = Fq::zero();
        let n = self.0.len() as u64;
        for i in 1..=n {
            v += Fq::from(self.0[(i - 1) as usize]) * (r.0).pow(&[i - 1]);
        }
        Evaluation(v)
    }
}

/// `ChallengeElement` is where both parties evaluate.
pub struct ChallengeElement(pub Fq);

/// `Evaluation` is the result of a polynomial evauated at a `ChallengeElement`.
#[derive(PartialEq)]
pub struct Evaluation(pub Fq);

pub struct Prover {
    pub data: RawData,
}

impl Prover {
    pub fn run<R: RngCore>(&self, rng: &mut R) -> (Evaluation, ChallengeElement) {
        let r = ChallengeElement(Fq::rand(rng));
        (self.data.reed_solomon_encoding(&r), r)
    }
}

pub struct Verifier {
    pub data: RawData,
}

impl Verifier {
    pub fn run(&self, r: ChallengeElement, v: Evaluation) -> bool {
        v == self.data.reed_solomon_encoding(&r)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use rand_core::OsRng;

    #[test]
    fn reed_solomon_equal() {
        let alice_data = RawData(vec![1, 2, 3]);
        let bob_data = RawData(vec![1, 2, 3]);
        let prover = Prover { data: alice_data };
        let verifier = Verifier { data: bob_data };
        let (r, v) = prover.run(&mut OsRng);
        assert!(verifier.run(v, r));
    }

    #[test]
    fn reed_solomon_not_equal() {
        let alice_data = RawData(vec![1, 2, 3]);
        let bob_data = RawData(vec![4, 5, 6]);
        let prover = Prover { data: alice_data };
        let verifier = Verifier { data: bob_data };
        let (r, v) = prover.run(&mut OsRng);
        assert!(!verifier.run(v, r));
    }
}
