/*
This is an example Overpass query.
Try it out by pressing the Run button above!
You can find more examples with the Load tool.
*/
node["highway"="speed_limit"](around:1000, 43.792879, -79.314193);
node["traffic_sign"](around:1000, 43.792879, -79.314193);
out body;