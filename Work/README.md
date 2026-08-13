dSpace troubleshooting page: https://www.dspace.com/en/pub/home/support/kb/dskpr/kprsfc.cfm



function crossings = fcn(angle)

persistent crossings_prev

if isempty(crossings_prev)
    crossings_prev = 0;
end

% Default output
crossings = crossings_prev;

% Detect zero crossing
if angle == 0
    crossings_prev = crossings_prev + 1;
    crossings = crossings_prev;
end

end

https://de.mathworks.com/help/vdynblks/ug/two-axle-tractor-towing-a-two-axle-trailer.html

https://de.mathworks.com/help/driving/ref/simulation3dvehiclewithgroundfollowing.html
