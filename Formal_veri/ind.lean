def line (spaces stars : Nat) : String :=
  String.intercalate "" (
    (List.range spaces).map (fun _ => " ") ++
    (List.range stars).map (fun _ => "*")
  )

def pattern : String :=
  let lines :=
    List.foldl (fun acc i =>
      acc ++
      match i with
      | 0 => [line 2 1]
      | 1 => [line 1 3]
      | 2 => [line 0 5]
      | 3 => [line 2 1]
      | 4 => [line 2 1]
      | _ => []
    ) [] (List.range 5)

  String.intercalate "\n" lines

def pattern2 : String :=
  let shapes := [(2,1), (1,3), (0,5), (2,1), (2,1)]
  let lines :=
    shapes.map (fun (s, st) => line s st)
  String.intercalate "\n" lines
#eval pattern2



structure Point where
  x : Nat
  y : Nat

def f (p : Point) : Point :=
  if p.x > p.y then
    { x := p.y, y := p.x }
  else
    p


#eval f {x:=57, y:=56}


inductive Tree where
  | leaf (x : Nat)
  | branch (x : Nat) (left right : Tree)
def sumTree : Tree → Nat
  | .leaf x => x
  | .branch x left right => x + (sumTree left) + (sumTree right)

#eval sumTree (.branch 5 (.leaf 0) (.leaf 2))

def inOrder : Tree → List Nat
    |.leaf xs => [xs]
    |.branch xs left right => inOrder left ++  [xs]  ++ inOrder right


def preOrder : Tree → List Nat
    |.leaf xs => [xs]
    | .branch xs left right => [xs] ++ inOrder left ++ inOrder right

def postOrder : Tree → List Nat
    |.leaf xs => [xs]
    | .branch xs left right => postOrder right ++ postOrder left ++ [xs]

-----Ex1--------
def cube (x:Nat) := x*x
#eval cube 5

def collatz (x:Nat) :=
    if (x%2==0) then
        x/2
    else
      (3*x+1)/2
#eval collatz 6


---Ex2--------
def collatz_calc (fuel x:Nat): Nat :=
  match fuel with
  |0=>x
  |n+1 =>
    if x=1 then
      1
    else
      collatz_calc n (collatz x)

#eval collatz_calc 100 7


structure Point3 where
  x:Nat
  y:Nat
  z:Nat


def sortList [DecidableEq α] (x:α):
    List (List α) → List (List α)
    |[] => [[x]]
    |(g::gs) =>
      match g with
      |[] => sortList x gs
      | y:: _=>
        if x = y then
            (x::g)::gs
        else
          g::sortList x gs
def group {α} [DecidableEq α] (xs: List α) : List (List α):=
  xs.foldl (fun acc x => sortList x acc) []

def dup {α} : List α → List α
  | [] => []
  | x :: xs => x :: x :: dup xs



structure Complex where
  x : Int
  y : Int
  deriving BEq

def mkComplex (x y : Int) : Complex :=
  { x := x, y := y }

def complex2string (c : Complex) : String :=
  toString c.x ++ " + " ++ toString c.y ++ "i"


#eval complex2string (mkComplex 2 4)

-- "3 + 4i"


-----IO and exception handling-------
def fallible (n:Nat) : IO Unit := do
  if n==0 then
    throw (.userError "I cannot process 0")
  else
    IO.println s!"{n}"

def catching : IO Unit := do
  try
    fallible 5
    fallible  0
  catch ex =>
    IO.println s!"{ex.toString}"


#eval catching




theorem f2f : 42 =42:= by
  simp

theorem add_zero (n:Nat) :
  n + 0 =n :=
  by
    rfl


def sumTo: List Nat →  Nat
  |[] => 0
  | x::xs => x + sumTo xs

