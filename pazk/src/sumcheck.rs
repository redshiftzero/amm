use anyhow::Error;
use ark_bls12_377::Fq;

/// Toy polynomial g(X, Y, Z) = X^2 Y^2 Z
pub struct ToyPolynomial {
    pub X: u64,
    pub Y: u64,
    pub Z: u64,
}

impl ToyPolynomial {
    /// Evaluate this polynomial over the boolean hypercube, i.e. g(b_1, b_2, b_3)
    pub fn evaluate(&self) -> u64 {
        let mut tot = 0;
        for b_1 in 0u64..=1 {
            for b_2 in 0u64..=1 {
                for b_3 in 0..=1 {
                    tot += b_1.pow(2u32) * b_2.pow(2u32) * b_3
                }
            }
        }
        tot
    }
}

pub struct Prover {}

pub struct ProverPolynomial {}

pub struct ChallengeElement(pub Fq);

impl Prover {
    /// At the start of the protocol, prover sends C_1 which is equal to H
    pub fn setup(&self) -> Fq {
        todo!()
    }

    /// In the first round, the Prover sends g_1(X_1)
    pub fn first_round(&self) -> ProverPolynomial {
        todo!()
    }

    /// In the jth round, the verifier sends g_j(X_j)
    pub fn jth_round(&self, r_j_minus_1: ChallengeElement) -> ProverPolynomial {
        todo!()
    }
}

pub struct Verifier {}

impl Verifier {
    /// Verifier saves C_1
    pub fn set_C1(&self, C_1: Fq) {
        todo!()
    }

    /// Verifier checks that C_1 = g_1(0) + g_1(1)
    pub fn process_first_round(&mut self, message: &ProverPolynomial) -> Result<(), Error> {
        todo!()
    }

    /// V chooses a random challenge element in the field
    pub fn generate_challenge(&mut self) -> ChallengeElement {
        todo!()
    }

    /// V processes jth round
    pub fn process_jth_round(&self, message: &ProverPolynomial) -> Result<(), Error> {
        todo!()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use rand_core::OsRng;

    #[test]
    fn sumcheck_example_execution_honest_prover() {
        let mut prover = Prover {};
        let mut verifier = Verifier {};
        let mut poly = ToyPolynomial { X: 1, Y: 1, Z: 1 };
        assert_eq!(poly.evaluate(), 1);

        let C_1 = prover.setup();
        verifier.set_C1(C_1);

        let round_1 = prover.first_round();
        verifier.process_first_round(&round_1).is_ok();
        let challenge_1 = verifier.generate_challenge();

        // Do this in a loop
        let round_j = prover.jth_round(challenge_1);
        verifier.process_jth_round(&round_j).is_ok();
        let challenge_j = verifier.generate_challenge();

        // TODO end
    }
}
