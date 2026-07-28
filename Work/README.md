function crossings = fcn(angle)

persistent crossings_prev

if isempty(crossings_prev)
    crossings_prev = 0;
else
    if angle==0
        crossings = crossings_prev + 1;
    else
        crossings = crossings_prev;
    end
end


end

