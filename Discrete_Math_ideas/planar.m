k = 4;          % k even
n = 2*k;

edges = [];

% almost-cycle edges, except (k-2,k-1)
for i = 1:n-1
    if i ~= k-2
        edges = [edges; i i+1];
    end
end
edges = [edges; n 1];

% long chords
edges = [edges; 1 k];

for i = 2:k-1
    edges = [edges; i i+k+1];
end

% two middle chords
edges = [edges; k-2 k+1];
edges = [edges; k-1 k+2];
figure
G = graph(edges(:,1), edges(:,2));
plot(G,'Layout','force');