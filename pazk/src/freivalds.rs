use ark_bls12_377::Fq;
use ark_ff::{Field, UniformRand};
use nalgebra::{DMatrix, DVector};
use rand_core::RngCore;

/// `Prover` computes `C = A * B`
pub struct Prover {
    pub A: DMatrix<Fq>,
    pub B: DMatrix<Fq>,
    pub C: DMatrix<Fq>,
}

/// `Verifier` computes `C * x` and `(AB)x`
pub struct Verifier {
    pub A: DMatrix<Fq>,
    pub B: DMatrix<Fq>,
    pub C: DMatrix<Fq>,
}

impl Verifier {
    pub fn run<R: RngCore>(&self, rng: &mut R) -> bool {
        let r = Fq::rand(rng);
        let n = self.C.nrows();
        let x_vec: Vec<Fq> = (0..n)
            .into_iter()
            .map(|i| (r).pow(&[(i + 1) as u64]))
            .collect();
        let x = DVector::from_row_slice(&x_vec);
        let Cx = self.C.clone() * x.clone();
        let ABx = self.A.clone() * (self.B.clone() * x);
        Cx == ABx
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use rand_core::OsRng;

    #[test]
    fn matmul_equal() {
        let fq_iter = (1..10).map(|i| Fq::from(i));
        let A = DMatrix::from_iterator(3, 3, fq_iter.clone());
        let B = DMatrix::from_iterator(3, 3, fq_iter);
        let correct_C = A.clone() * B.clone();
        let prover = Prover {
            A: A.clone(),
            B: B.clone(),
            C: correct_C.clone(),
        };
        let verifier = Verifier { A, B, C: correct_C };
        assert!(verifier.run(&mut OsRng));
    }

    #[test]
    fn matmul_not_equal() {
        let fq_iter = (1..10).map(|i| Fq::from(i));
        let A = DMatrix::from_iterator(3, 3, fq_iter.clone());
        let B = DMatrix::from_iterator(3, 3, fq_iter);
        let incorrect_C = B.clone();
        let prover = Prover {
            A: A.clone(),
            B: B.clone(),
            C: incorrect_C.clone(),
        };
        let verifier = Verifier {
            A,
            B,
            C: incorrect_C,
        };
        assert!(!verifier.run(&mut OsRng));
    }
}
