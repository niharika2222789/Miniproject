let map;
let userLoc;
let currentMarker = null;
let directionsService;
let directionsRenderer;
let mode = "city";

let disasterMarkers = [];

// ✅ FIXED (comma added + mumbai added)
const cities = {
  hyderabad: { lat: 17.385044, lng: 78.486671 },
  delhi: { lat: 28.6139, lng: 77.2090 },
  mumbai: { lat: 19.0760, lng: 72.8777 },
  chennai: { lat: 13.0827, lng: 80.2707 },
  jammu_kashmir: { lat: 34.0837, lng: 74.7973 }
};


// 📍 DELHI DISASTER DATA (same as yours)
const delhiData = [
  { name: "Seelampur", lat: 28.6692, lng: 77.2660, disaster: "Flood + Epidemic", level: "High", reason: "Dense population" },
  { name: "Sadar Bazaar", lat: 28.6590, lng: 77.2160, disaster: "Earthquake", level: "High", reason: "Old buildings" },
  { name: "Mayur Vihar Phase 1", lat: 28.6060, lng: 77.2950, disaster: "Flood", level: "High", reason: "Near Yamuna" },
  { name: "ITO", lat: 28.6289, lng: 77.2420, disaster: "Urban Flooding", level: "High", reason: "Waterlogging hotspot" },
  { name: "Minto Bridge", lat: 28.6300, lng: 77.2200, disaster: "Waterlogging", level: "High", reason: "Frequent flooding" },
  { name: "Chandni Chowk", lat: 28.6562, lng: 77.2303, disaster: "Fire Hazard", level: "High", reason: "Dense market" },
  { name: "Bawana Industrial Area", lat: 28.8040, lng: 77.0480, disaster: "Chemical Hazard", level: "High", reason: "Industrial zone" },
  { name: "Connaught Place", lat: 28.6315, lng: 77.2167, disaster: "Terror Sensitive", level: "High", reason: "Central hub" },

  { name: "Dwarka", lat: 28.5921, lng: 77.0460, disaster: "Thunderstorm", level: "Medium", reason: "Open area" },
  { name: "Rohini", lat: 28.7041, lng: 77.1025, disaster: "Dust Storm", level: "Medium", reason: "Outer winds" },
  { name: "Najafgarh", lat: 28.6090, lng: 76.9855, disaster: "Cold Wave", level: "Medium", reason: "Low temp zone" },
  { name: "Paharganj", lat: 28.6448, lng: 77.2167, disaster: "Building Collapse", level: "Medium", reason: "Old structures" },
  { name: "Karol Bagh", lat: 28.6519, lng: 77.1909, disaster: "Heatwave", level: "Medium", reason: "Urban heat" },
  { name: "AIIMS Area", lat: 28.5672, lng: 77.2100, disaster: "Road Accidents", level: "Medium", reason: "Heavy traffic" },

  { name: "India Gate", lat: 28.6129, lng: 77.2295, disaster: "Low Risk Zone", level: "Low", reason: "Planned area" },
  { name: "Chanakyapuri", lat: 28.5933, lng: 77.1883, disaster: "Low Risk Zone", level: "Low", reason: "Diplomatic zone" },
  { name: "Aerocity", lat: 28.5485, lng: 77.1220, disaster: "Low Risk Zone", level: "Low", reason: "Modern infra" },
  { name: "Vasant Kunj", lat: 28.5245, lng: 77.1587, disaster: "Low Risk Zone", level: "Low", reason: "Low density" },
  { name: "Saket", lat: 28.5244, lng: 77.2066, disaster: "Low Risk Zone", level: "Low", reason: "Planned" },
  { name: "Janakpuri", lat: 28.6219, lng: 77.0878, disaster: "Low Risk Zone", level: "Low", reason: "Organized layout" }
];

// 🔥 NEW: HYDERABAD DATA
const hyderabadData = [
  { name: "Chaderghat", lat: 17.3731, lng: 78.4867, disaster: "Flood", level: "High", reason: "Musi River zone" },
  { name: "Afzalgunj", lat: 17.3715, lng: 78.4747, disaster: "Flood", level: "High", reason: "Low-lying area" },
  { name: "Dabirpura", lat: 17.3688, lng: 78.4965, disaster: "Flood + Waterlogging", level: "High", reason: "Drainage issue" },
  { name: "Tolichowki", lat: 17.4039, lng: 78.4006, disaster: "Urban Flooding", level: "High", reason: "Rapid urbanization" },
  { name: "Kukatpally", lat: 17.4948, lng: 78.3996, disaster: "Flood", level: "High", reason: "Lake overflow" },
  { name: "LB Nagar", lat: 17.3457, lng: 78.5570, disaster: "Flood", level: "High", reason: "Water accumulation" },
  { name: "Charminar", lat: 17.3616, lng: 78.4747, disaster: "Fire + Collapse", level: "High", reason: "Dense structures" },
  { name: "Jeedimetla", lat: 17.5150, lng: 78.4500, disaster: "Chemical Hazard", level: "High", reason: "Industrial zone" },

  { name: "Ameerpet", lat: 17.4375, lng: 78.4483, disaster: "Urban Flood", level: "Medium", reason: "Drainage stress" },
  { name: "Begumpet", lat: 17.4447, lng: 78.4667, disaster: "Waterlogging", level: "Medium", reason: "Low elevation" },
  { name: "Madhapur", lat: 17.4483, lng: 78.3915, disaster: "Urban Flood", level: "Medium", reason: "Dense IT zone" },
  { name: "Mehdipatnam", lat: 17.3950, lng: 78.4390, disaster: "Traffic + Flood", level: "Medium", reason: "Heavy junction" },
  { name: "Uppal", lat: 17.4050, lng: 78.5590, disaster: "Flood", level: "Medium", reason: "Lake nearby" },
  { name: "Nagole", lat: 17.3715, lng: 78.5685, disaster: "Waterlogging", level: "Medium", reason: "Expansion area" },

  { name: "Banjara Hills", lat: 17.4126, lng: 78.4482, disaster: "Low Risk", level: "Low", reason: "Elevated area" },
  { name: "Jubilee Hills", lat: 17.4239, lng: 78.4070, disaster: "Low Risk", level: "Low", reason: "Planned zone" },
  { name: "Gachibowli", lat: 17.4401, lng: 78.3489, disaster: "Low Risk", level: "Low", reason: "Modern infra" },
  { name: "Financial District", lat: 17.4116, lng: 78.3380, disaster: "Low Risk", level: "Low", reason: "Tech zone" },
  { name: "Secunderabad", lat: 17.4399, lng: 78.4983, disaster: "Low Risk", level: "Low", reason: "Organized area" },
  { name: "Shamshabad", lat: 17.2403, lng: 78.4294, disaster: "Low Risk", level: "Low", reason: "Open area" }
];

// ================== MUMBAI DATA ==================
const mumbaiData = [
  { name: "Kurla", lat: 19.0726, lng: 72.8826, disaster: "Flood", level: "High", reason: "Mithi River overflow" },
  { name: "Sion", lat: 19.0430, lng: 72.8619, disaster: "Flood", level: "High", reason: "Low-lying area" },
  { name: "Dharavi", lat: 19.0444, lng: 72.8553, disaster: "Flood + Epidemic", level: "High", reason: "Dense slum" },
  { name: "Andheri Subway", lat: 19.1197, lng: 72.8464, disaster: "Waterlogging", level: "High", reason: "Flood hotspot" },
  { name: "BKC", lat: 19.0600, lng: 72.8656, disaster: "Flood", level: "High", reason: "Reclaimed land" },
  { name: "Chembur", lat: 19.0522, lng: 72.9005, disaster: "Chemical Hazard", level: "High", reason: "Industrial zone" },
  { name: "Byculla", lat: 18.9766, lng: 72.8331, disaster: "Building Collapse", level: "High", reason: "Old buildings" },
  { name: "Nariman Point", lat: 18.9220, lng: 72.8347, disaster: "Coastal Flood", level: "High", reason: "Sea-facing" },

  { name: "Dadar", lat: 19.0176, lng: 72.8562, disaster: "Flood + Crowd", level: "Medium", reason: "Transport hub" },
  { name: "Ghatkopar", lat: 19.0850, lng: 72.9080, disaster: "Landslide", level: "Medium", reason: "Hilly terrain" },
  { name: "Mulund", lat: 19.1726, lng: 72.9560, disaster: "Landslide", level: "Medium", reason: "Hill slopes" },
  { name: "Powai", lat: 19.1176, lng: 72.9060, disaster: "Flood", level: "Medium", reason: "Lake overflow" },
  { name: "Jogeshwari", lat: 19.1340, lng: 72.8488, disaster: "Waterlogging", level: "Medium", reason: "Drainage issue" },
  { name: "Vikhroli", lat: 19.1100, lng: 72.9400, disaster: "Industrial + Flood", level: "Medium", reason: "Mixed zone" },

  { name: "Colaba", lat: 18.9067, lng: 72.8147, disaster: "Low Risk", level: "Low", reason: "Planned zone" },
  { name: "Malabar Hill", lat: 18.9520, lng: 72.7956, disaster: "Low Risk", level: "Low", reason: "Elevated" },
  { name: "Churchgate", lat: 18.9322, lng: 72.8264, disaster: "Low Risk", level: "Low", reason: "Strong infra" },
  { name: "Marine Drive", lat: 18.9430, lng: 72.8238, disaster: "Low Risk", level: "Low", reason: "Coastal protection" },
  { name: "Juhu", lat: 19.1075, lng: 72.8263, disaster: "Low Risk", level: "Low", reason: "Open layout" },
  { name: "Borivali", lat: 19.2307, lng: 72.8567, disaster: "Low Risk", level: "Low", reason: "Less dense" }
];

// =======================
// 🏔 JAMMU & KASHMIR DATA
// =======================

const jammuKashmirData = [
  // 🔴 HIGH RISK
  { name: "Srinagar", lat: 34.0837, lng: 74.7973, disaster: "Flood + Urban Flood", level: "high" },
  { name: "Anantnag", lat: 33.7311, lng: 75.1542, disaster: "Flood + Landslide", level: "high" },
  { name: "Baramulla", lat: 34.2000, lng: 74.3500, disaster: "Flood + Earthquake", level: "high" },
  { name: "Kupwara", lat: 34.5300, lng: 74.2600, disaster: "Landslide + Earthquake", level: "high" },
  { name: "Kishtwar", lat: 33.3130, lng: 75.7670, disaster: "Landslide + Earthquake", level: "high" },
  { name: "Ramban", lat: 33.2420, lng: 75.2390, disaster: "Landslide", level: "high" },
  { name: "Ganderbal", lat: 34.2260, lng: 74.7800, disaster: "Cloudburst + Flash Flood", level: "high" },
  { name: "Bandipora", lat: 34.4170, lng: 74.6430, disaster: "Avalanche + Snowstorm", level: "high" },

  // 🟠 MEDIUM RISK
  { name: "Pulwama", lat: 33.8740, lng: 74.8990, disaster: "Flood + Earthquake", level: "medium" },
  { name: "Budgam", lat: 34.0230, lng: 74.7740, disaster: "Flood + Cold Wave", level: "medium" },
  { name: "Shopian", lat: 33.7170, lng: 74.8330, disaster: "Snowfall + Landslide", level: "medium" },
  { name: "Poonch", lat: 33.7700, lng: 74.0900, disaster: "Landslide + Heavy Rain", level: "medium" },
  { name: "Rajouri", lat: 33.3800, lng: 74.3100, disaster: "Earthquake + Storm", level: "medium" },
  { name: "Doda", lat: 33.1460, lng: 75.5480, disaster: "Landslide + Earthquake", level: "medium" },

  // 🟢 LOW RISK
  { name: "Jammu", lat: 32.7266, lng: 74.8570, disaster: "Heatwave + Minor Flood", level: "low" },
  { name: "Udhampur", lat: 32.9240, lng: 75.1350, disaster: "Road Accidents", level: "low" },
  { name: "Kathua", lat: 32.3690, lng: 75.5250, disaster: "Heatwave", level: "low" },
  { name: "Samba", lat: 32.5620, lng: 75.1190, disaster: "Industrial Hazard", level: "low" },
  { name: "Reasi", lat: 33.0800, lng: 74.8300, disaster: "Minor Landslide", level: "low" },
  { name: "Kargil", lat: 34.5550, lng: 76.1340, disaster: "Cold Desert Risk", level: "low" }
];

const chennaiData = [
  { name:"Ennore", lat:13.2146, lng:80.3203, disaster:"Cyclone + Flood", level:"High", reason:"Coastal zone" },
  { name:"Kasimedu", lat:13.1205, lng:80.2942, disaster:"Storm Surge", level:"High", reason:"Fishing harbor" },
  { name:"Royapuram", lat:13.1137, lng:80.2954, disaster:"Flood", level:"High", reason:"Low lying" },
  { name:"Tondiarpet", lat:13.1261, lng:80.2886, disaster:"Cyclone", level:"High", reason:"Dense settlements" },
  { name:"Basin Bridge", lat:13.0995, lng:80.2704, disaster:"Urban Flood", level:"High", reason:"Drainage overflow" },
  { name:"Besant Nagar", lat:13.0003, lng:80.2667, disaster:"Tsunami Risk", level:"High", reason:"Beachfront" },
  { name:"Velachery", lat:12.9791, lng:80.2209, disaster:"Flood", level:"High", reason:"Waterlogging hotspot" },
  { name:"Foreshore Estate", lat:13.0205, lng:80.2758, disaster:"Cyclone", level:"High", reason:"Sea exposure" },

  { name:"Perambur", lat:13.1067, lng:80.2337, disaster:"Flood", level:"Medium", reason:"Drainage issue" },
  { name:"Kolathur", lat:13.1246, lng:80.2150, disaster:"Flood", level:"Medium", reason:"Lake overflow" },
  { name:"Ambattur", lat:13.1143, lng:80.1548, disaster:"Urban Flood", level:"Medium", reason:"Industrial area" },
  { name:"Porur", lat:13.0381, lng:80.1565, disaster:"Flood", level:"Medium", reason:"Lake nearby" },
  { name:"Pallikaranai", lat:12.9497, lng:80.2130, disaster:"Flood", level:"Medium", reason:"Marshland" },
  { name:"Maduravoyal", lat:13.0657, lng:80.1700, disaster:"Flood", level:"Medium", reason:"Low elevation" },

  { name:"Anna Nagar", lat:13.0850, lng:80.2101, disaster:"Low Risk", level:"Low", reason:"Planned area" },
  { name:"Mogappair", lat:13.0835, lng:80.1750, disaster:"Low Risk", level:"Low", reason:"Modern infra" },
  { name:"Nungambakkam", lat:13.0604, lng:80.2496, disaster:"Low Risk", level:"Low", reason:"Central zone" },
  { name:"Adyar", lat:13.0067, lng:80.2574, disaster:"Low Risk", level:"Low", reason:"Managed drainage" },
  { name:"Thiruvanmiyur", lat:12.9830, lng:80.2594, disaster:"Low Risk", level:"Low", reason:"Open layout" },
  { name:"Ashok Nagar", lat:13.0350, lng:80.2120, disaster:"Low Risk", level:"Low", reason:"Planned roads" }
];
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: cities.hyderabad,
    zoom: 12,
    styles: [{ featureType: "poi", stylers: [{ visibility: "off" }] }]
  });

  directionsService = new google.maps.DirectionsService();
  directionsRenderer = new google.maps.DirectionsRenderer({ map });

  setMarker(cities.hyderabad, "HYDERABAD");

  // 🔥 LOAD HYDERABAD BY DEFAULT
  loadHyderabadDisasters();
}

// 🎨 ICON COLORS
function getIcon(level) {
  if (level === "High") return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
  if (level === "Medium") return "http://maps.google.com/mapfiles/ms/icons/orange-dot.png";
  return "http://maps.google.com/mapfiles/ms/icons/green-dot.png";
}

// 🧹 CLEAR
function clearMap() {
  if (currentMarker) currentMarker.setMap(null);
  directionsRenderer.setDirections({ routes: [] });

  disasterMarkers.forEach(m => m.setMap(null));
  disasterMarkers = [];
}

// 📍 DEFAULT MARKER
function setMarker(location, title) {
  currentMarker = new google.maps.Marker({
    position: location,
    map: map,
    title: title,
  });
  map.setCenter(location);
}

// 🔥 HYDERABAD MARKERS
function loadHyderabadDisasters() {
  hyderabadData.forEach(loc => {
    const marker = new google.maps.Marker({
      position: { lat: loc.lat, lng: loc.lng },
      map: map,
      icon: getIcon(loc.level),
      title: loc.name
    });

    marker.level = loc.level;

    const info = new google.maps.InfoWindow({
      content: `
        <div style="font-family: Arial; padding:10px;">
          <h3>📍 ${loc.name}</h3>
          <p><b>Disaster:</b> ${loc.disaster}</p>
          <p><b>Risk Level:</b> ${loc.level}</p>
          <p><b>Reason:</b> ${loc.reason}</p>
        </div>
      `
    });

    marker.addListener("click", () => info.open(map, marker));

    disasterMarkers.push(marker);
  });
}

// 🔥 EXISTING FUNCTIONS (UNCHANGED BELOW) :contentReference[oaicite:0]{index=0}

// 🔥 ADD DELHI MARKERS + STORE LEVEL
function loadDelhiDisasters() {
  delhiData.forEach(loc => {
    const marker = new google.maps.Marker({
      position: { lat: loc.lat, lng: loc.lng },
      map: map,
      icon: getIcon(loc.level),
      title: loc.name
    });

    marker.level = loc.level;

    const info = new google.maps.InfoWindow({
      content: `
        <div style="font-family: Arial; padding:10px;">
          <h3>📍 ${loc.name}</h3>
          <p><b>Disaster:</b> ${loc.disaster}</p>
          <p><b>Risk Level:</b> ${loc.level}</p>
          <p><b>Reason:</b> ${loc.reason}</p>
        </div>
      `
    });

    marker.addListener("click", () => info.open(map, marker));

    disasterMarkers.push(marker);
  });
}
// 🔥 MUMBAI MARKERS (ADDED)
function loadMumbaiDisasters() {
  mumbaiData.forEach(loc => {
    const marker = new google.maps.Marker({
      position: { lat: loc.lat, lng: loc.lng },
      map: map,
      icon: getIcon(loc.level),
      title: loc.name
    });

    marker.level = loc.level;

    const info = new google.maps.InfoWindow({
      content: `
        <div style="font-family: Arial; padding:10px;">
          <h3>📍 ${loc.name}</h3>
          <p><b>Disaster:</b> ${loc.disaster}</p>
          <p><b>Risk Level:</b> ${loc.level}</p>
          <p><b>Reason:</b> ${loc.reason}</p>
        </div>
      `
    });

    marker.addListener("click", () => info.open(map, marker));

    disasterMarkers.push(marker);
  });
}
function loadChennaiDisasters() {
  chennaiData.forEach(loc => {

    const marker = new google.maps.Marker({
      position: { lat: loc.lat, lng: loc.lng },
      map: map,
      icon: getIcon(loc.level),
      title: loc.name
    });

    marker.level = loc.level;

    const info = new google.maps.InfoWindow({
      content: `
        <div style="padding:10px">
          <h3>${loc.name}</h3>
          <p><b>Disaster:</b> ${loc.disaster}</p>
          <p><b>Risk:</b> ${loc.level}</p>
          <p><b>Reason:</b> ${loc.reason}</p>
        </div>
      `
    });

    marker.addListener("click", () => info.open(map, marker));

    disasterMarkers.push(marker);
  });
}
function loadJammuDisasters() {

  jammuKashmirData.forEach(loc => {

    const risk =
      loc.level === "high" ? "High" :
      loc.level === "medium" ? "Medium" : "Low";

    const marker = new google.maps.Marker({
      position: { lat: loc.lat, lng: loc.lng },
      map: map,
      icon: getIcon(risk),
      title: loc.name
    });

    marker.level = risk;

    const info = new google.maps.InfoWindow({
      content: `
        <div style="padding:10px">
          <h3>${loc.name}</h3>
          <p><b>Disaster:</b> ${loc.disaster}</p>
          <p><b>Risk:</b> ${risk}</p>
        </div>
      `
    });

    marker.addListener("click", () => info.open(map, marker));

    disasterMarkers.push(marker);
  });
}

// 🔥 TOGGLE FILTER FUNCTION
function filterMarkers(level) {
  disasterMarkers.forEach(marker => {
    if (level === "all") {
      marker.setMap(map);
    } else if (marker.level === level) {
      marker.setMap(map);
    } else {
      marker.setMap(null);
    }
  });
}

// 📍 CURRENT LOCATION
function loadCurrentLocation() {
  mode = "current";

  navigator.geolocation.getCurrentPosition(pos => {
    userLoc = {
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
    };

    clearMap();
    setMarker(userLoc, "You 📍");
    map.setZoom(14);
  });
}

// 🌆 SWITCH
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("citySelect").addEventListener("change", function () {
    const value = this.value;

    clearMap();

    if (value === "current") {
      loadCurrentLocation();
  } else if (value === "delhi") {
  map.setCenter(cities.delhi);
  map.setZoom(11);
  loadDelhiDisasters();

} else if (value === "mumbai") { // 🔥 ADDED
  map.setCenter(cities.mumbai);
  map.setZoom(11);
  loadMumbaiDisasters();
} else if (value === "chennai") {

  map.setCenter(cities.chennai);
  map.setZoom(11);
  loadChennaiDisasters();

} else if (value === "jammu_kashmir") {

  map.setCenter(cities.jammu_kashmir);
  map.setZoom(8);
  loadJammuDisasters();

} else {
      setMarker(cities.hyderabad, "HYDERABAD");
      map.setZoom(12);
      loadHyderabadDisasters(); // 🔥 ADDED
    }
  });
});
