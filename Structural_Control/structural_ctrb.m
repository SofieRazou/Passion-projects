% n = input("Enter system size");
% p = input("Enter controls size");
% A = input("Enter system matrix");
% B = input("Enter input matrix");
% C = input("Enter output matrix");
% D = input("Enter feedforward matrix");
k = 10;
b = 0.05;
m = 1.5;

A = [0 1 0; -k/m -b/m 1; 0 0 0];
B = [0;0;0];
C = [1 0 0];
D = 0;
n = 2;
p = 1;
%construct state-space for later benchmarking
% sys = ss(A,B,C,D);
% C = ctrb(sys);
% if rank(C)==(n+p)
%     disp("Your entered system is controllable");
% else
%     disp("The entered system is not controllable");
% end 


[row1, col1] = find(A);
% [row2, col2] = find(B);
%construct interconnection graph
s1 = row1;
t1 = col1;
G1 = digraph(s1,t1);

%flip control-state edges
edgeID = findedge(G1, 2, 3);
G1 = flipedge(G1,edgeID);

figure;
plot(G1);


%necessary condition for structural controllability
function [is_reachable,v] = reach(G, n, p)
         for node=1:(n+p)
             if indegree(G, node)==0
                  start_node = node;
                  break;
             end
         end
         v = bfsearch(G,start_node);
         if ~(size(v)==n+p)
             is_reachable = false;
         else
             is_reachable = true;
         end

end

[nec_condition,v] = reach(G1, n, p);
if nec_condition == 0
    disp("System is non-controllable");
else
    disp("System could be controllable");
end 


%perform sufficient condition check 
function [is_maxed_matched, max_matching] = check_matching(G, n)

    % Build adjacency list
    edges = G.Edges.EndNodes;

    nLeft = numnodes(G);
    adj = cell(nLeft,1);
    
    for k = 1:size(edges,1)
    
        u = edges(k,1);
        v = edges(k,2);
    
        adj{u} = [adj{u}, v];

    end

    % Initialize matching
    Pair_U = zeros(n,1);
    Pair_V = zeros(n,1);

    matching_size = 0;

    % NIL represents an unmatched vertex
    NIL = n + 1;
    dist = inf(n+1,1);

    % Main Hopcroft-Karp loop
    while BFS()

        for u = 1:n
            if Pair_U(u) == 0
                if DFS(u)
                    matching_size = matching_size + 1;
                end
            end
        end

    end

    % Return the matching pairs [left vertex, right vertex]
    matched_U = find(Pair_U ~= 0);
    max_matching = [matched_U, Pair_U(matched_U)];

    is_maxed_matched = (matching_size == n);


    %---------------- BFS ----------------%

    function found = BFS()

        queue = zeros(n,1);
        head = 1;
        tail = 0;

        dist(:) = inf;

        % Start from all unmatched left vertices
        for u = 1:n
            if Pair_U(u) == 0
                tail = tail + 1;
                queue(tail) = u;
                dist(u) = 0;
            end
        end

        dist(NIL) = inf;

        while head <= tail

            u = queue(head);
            head = head + 1;

            if dist(u) < dist(NIL)

                for v = adj{u}

                    next_u = Pair_V(v);

                    if next_u == 0
                        next_u = NIL;
                    end

                    if dist(next_u) == inf

                        dist(next_u) = dist(u) + 1;

                        if next_u ~= NIL
                            tail = tail + 1;
                            queue(tail) = next_u;
                        end

                    end
                end
            end
        end

        found = (dist(NIL) ~= inf);

    end


    %---------------- DFS ----------------%

    function found = DFS(u)

        if u == NIL
            found = true;
            return;
        end

        found = false;

        for v = adj{u}

            next_u = Pair_V(v);

            if next_u == 0
                next_u = NIL;
            end

            if dist(next_u) == dist(u) + 1

                if DFS(next_u)

                    Pair_U(u) = v;
                    Pair_V(v) = u;

                    found = true;
                    return;

                end
            end
        end

        % Do not revisit this vertex in the current BFS phase
        dist(u) = inf;

    end

end

[suff, matching] = check_matching(G1, n);
if suff == true
    disp("IS CONTROLLABLE");
end