Undefined function or variable 's'.

Function 'to_be_transm_outputs/Pade/MATLAB Function' (#151.46.47), line 3, column 17:
"s"
Launch diagnostic report.
Component:MATLAB Function | Category:Coder error
Undefined function or variable 'y'. The first assignment to a local variable determines its class.

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

