clc;
clear;

%% TEST CASE
A = [0 0 0 0 2000 12 0;
     0 0 0 0 0 0 1;
     0 0 0 0 3 0 1;
     0 0 0 0 0 1 0;
     1 0 1 0 0 0 0;
     1 0 0 1 0 0 0;
     0 1 1 0 0 0 0
     ];

n = 4;
m = 3;

function A_extr = extract_weights(Amatrix)
    [rows, cols] = size(Amatrix);
     A_extr = zeros(rows, cols);
    for i=1:rows
        for j=1:cols
            if ~(Amatrix(i, j)==0)
                A_extr(i,j) = 1;
            end
           
        end
    end
end


%% CONSTRUCT ALL 2x2 BINARY BASE CASES

M = cell(16,1);
sp_values = zeros(16,1);

k = 1;

for a = 0:1
    for b = 0:1
        for c = 0:1
            for d = 0:1

                M{k} = [a b; c d];

                sp_values(k) = base_rank(M{k});

                k = k + 1;
            end
        end
    end
end

%% CALCULATE

Arank = sp_calc(A,M,sp_values);

disp("Calculated result:");
disp(Arank);


%% BASE CASE FUNCTION

function srank = base_rank(A)

    if all(A(:) == 0)
        srank = 0;

    elseif (A(1,1) && A(2,2)) || ...
           (A(1,2) && A(2,1))
        srank = 2;

    else
        srank = 1;
    end

end


%% LOOKUP FUNCTION

function index = find_matrix(X,M)

    index = find(cellfun(@(Y) isequal(X,Y),M),1);

    if isempty(index)
        error("Matrix not found in base cases.");
    end

end


%% PADDING FUNCTION

function A = pad_matrix(A)
    A = extract_weights(A);
    [r,c] = size(A);

    % Make matrix square
    s = max(r,c);

    A = [A zeros(r,s-c)];

    if r < s
        A = [A; zeros(s-r,s)];
    end

    % Make dimension even, so it can be divided
    if mod(s,2) ~= 0
        A = [A zeros(s,1)];
        A = [A; zeros(1,s+1)];
    end

end


%% RECURSIVE FUNCTION

function srank = sp_calc(A,M,sp_values)

    % Pad matrix before partitioning
    A = pad_matrix(A);

    [r,c] = size(A);

    % BASE CASE: 2x2
    if r == 2 && c == 2

        index = find_matrix(A,M);
        srank = sp_values(index);

        return;
    end

    % Divide matrix into four equal blocks
    mid = r/2;

    B1 = A(1:mid,1:mid);
    A1 = A(1:mid,mid+1:end);

    A2 = A(mid+1:end,1:mid);
    B2 = A(mid+1:end,mid+1:end);

    % Recursive calculations
    spB1 = sp_calc(B1,M,sp_values);
    spB2 = sp_calc(B2,M,sp_values);

    spA1 = sp_calc(A1,M,sp_values);
    spA2 = sp_calc(A2,M,sp_values);

    % Your proposed recurrence
    srank = max(spA1 + spA2, spB1 + spB2);

end

disp(sprank(A));