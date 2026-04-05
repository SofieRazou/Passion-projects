-- Girregular
inductive Alphabet where
  | a
  | b
deriving DecidableEq, Repr

abbrev word := List Alphabet

--  for a^n b^n

inductive Derive : word → Prop where
  | eps  : Derive []
  | step : Derive w → Derive (Alphabet.a :: w ++ [Alphabet.b])

def anbn : Nat → word
  | 0     => []
  | n + 1 => Alphabet.a :: anbn n ++ [Alphabet.b]

-- specification
def spec (w : word) : Prop :=
  ∃ n : Nat, w = anbn n

-- Completeness aka generates all valid strings

theorem completeness : ∀ n, Derive (anbn n) := by
  intro n
  induction n with
  | zero =>
      exact Derive.eps
  | succ n ih =>
      simp [anbn]
      exact Derive.step ih


-- Consistency only generates valid strings


theorem consistency : ∀ w, Derive w → spec w := by
  intro w h
  induction h with
  | eps =>
      exact ⟨0, rfl⟩
  | step h ih =>
      rcases ih with ⟨n, hn⟩
      refine ⟨n + 1, ?_⟩
      simp [anbn, hn, List.cons_append]
