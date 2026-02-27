// Mock data for Climate Smart Market Intelligence Platform
// Comprehensive market data matching AnoMura.today scope + Climate metrics

export const marketItems = [
  // VEGETABLES - Lettuce varieties
  { id: 1, name: "Lettuce (Romaine)", category: "vegetables", currentPrice: 168.77, averagePrice: 207, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 38.23, trend: [220, 210, 195, 185, 175, 168.77], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Favorable rainfall", "Optimal temperature"], forecast: "Prices expected to remain stable" }},
  { id: 2, name: "Lettuce (Green Ice)", category: "vegetables", currentPrice: 160.31, averagePrice: 173, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 12.69, trend: [180, 178, 172, 168, 164, 160.31], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Stable weather"], forecast: "Good supply" }},
  { id: 3, name: "Lettuce (Iceberg) Medium", category: "vegetables", currentPrice: 214.50, averagePrice: 230, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 15.50, trend: [240, 235, 228, 222, 218, 214.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good growing conditions"], forecast: "Steady supply" }},
  
  // VEGETABLES - Cabbage & Cruciferous
  { id: 4, name: "Cabbage (Rare Ball)", category: "vegetables", currentPrice: 73.41, averagePrice: 85, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 11.59, trend: [92, 88, 85, 80, 76, 73.41], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Excellent conditions"], forecast: "Abundant supply" }},
  { id: 5, name: "Cabbage (Scorpio)", category: "vegetables", currentPrice: 81.48, averagePrice: 85, unit: "kg", location: "NCR", icon: "🥬", status: "STABLE", savings: 3.52, trend: [88, 86, 84, 83, 82, 81.48], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal conditions"], forecast: "Stable supply" }},
  { id: 6, name: "Cabbage (Wonder Ball)", category: "vegetables", currentPrice: 75.97, averagePrice: 79, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 3.03, trend: [82, 81, 79, 78, 77, 75.97], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good harvest"], forecast: "Price declining" }},
  { id: 7, name: "Broccoli (Local Medium)", category: "vegetables", currentPrice: 144.67, averagePrice: 160, unit: "kg", location: "NCR", icon: "🥦", status: "MURA", savings: 15.33, trend: [165, 162, 158, 152, 148, 144.67], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Ideal growing conditions"], forecast: "Prices trending down" }},
  
  // VEGETABLES - Leafy greens
  { id: 8, name: "Pechay Baguio", category: "vegetables", currentPrice: 79.82, averagePrice: 84, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 4.18, trend: [88, 86, 84, 82, 81, 79.82], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal rainfall"], forecast: "Supply stable" }},
  { id: 9, name: "Pechay (Native)", category: "vegetables", currentPrice: 65.50, averagePrice: 72, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 6.50, trend: [75, 73, 71, 69, 67, 65.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good conditions"], forecast: "Plentiful" }},
  { id: 10, name: "Mustasa", category: "vegetables", currentPrice: 58.30, averagePrice: 62, unit: "kg", location: "NCR", icon: "🥬", status: "MURA", savings: 3.70, trend: [65, 64, 63, 61, 59, 58.30], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Steady production"], forecast: "Stable" }},
  
  // VEGETABLES - Onions
  { id: 11, name: "White Onion (Local)", category: "vegetables", currentPrice: 99.01, averagePrice: 105, unit: "kg", location: "NCR", icon: "🧅", status: "MURA", savings: 5.99, trend: [110, 108, 105, 102, 100, 99.01], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Post-harvest surplus"], forecast: "Prices stabilizing" }},
  { id: 12, name: "Red Onion (Imported)", category: "vegetables", currentPrice: 104.87, averagePrice: 110, unit: "kg", location: "NCR", icon: "🧅", status: "STABLE", savings: 5.13, trend: [115, 113, 111, 108, 106, 104.87], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Import stability"], forecast: "Dependent on global climate" }},
  { id: 13, name: "Red Onion (Local 13-15)", category: "vegetables", currentPrice: 117.37, averagePrice: 121, unit: "kg", location: "NCR", icon: "🧅", status: "STABLE", savings: 3.63, trend: [125, 123, 121, 119, 118, 117.37], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Local supply steady"], forecast: "Normal range" }},
  { id: 14, name: "Red Onion (Imported Medium)", category: "vegetables", currentPrice: 104.87, averagePrice: 110, unit: "kg", location: "NCR", icon: "🧅", status: "MURA", savings: 5.13, trend: [115, 112, 110, 107, 106, 104.87], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good imports"], forecast: "Stable" }},
  
  // VEGETABLES - Tomatoes
  { id: 15, name: "Tomato (Local)", category: "vegetables", currentPrice: 92.50, averagePrice: 105, unit: "kg", location: "NCR", icon: "🍅", status: "MURA", savings: 12.50, trend: [115, 110, 105, 100, 96, 92.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Optimal growing season"], forecast: "Peak harvest period" }},
  { id: 16, name: "Tomato 15-18 pcs/kg", category: "vegetables", currentPrice: 62.13, averagePrice: 65, unit: "kg", location: "NCR", icon: "🍅", status: "STABLE", savings: 2.87, trend: [68, 67, 66, 64, 63, 62.13], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good yield"], forecast: "Steady" }},
  
  // VEGETABLES - Peppers & Others
  { id: 17, name: "Chili (Green) Local", category: "vegetables", currentPrice: 101.23, averagePrice: 105, unit: "kg", location: "NCR", icon: "🌶️", status: "STABLE", savings: 3.77, trend: [108, 107, 106, 104, 102, 101.23], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal production"], forecast: "Stable" }},
  { id: 18, name: "Chili (Red) Local", category: "vegetables", currentPrice: 179.84, averagePrice: 184, unit: "kg", location: "NCR", icon: "🌶️", status: "STABLE", savings: 4.16, trend: [188, 186, 185, 182, 181, 179.84], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Seasonal variation"], forecast: "Holding steady" }},
  { id: 19, name: "Eggplant", category: "vegetables", currentPrice: 78.50, averagePrice: 82, unit: "kg", location: "NCR", icon: "🍆", status: "MURA", savings: 3.50, trend: [85, 84, 83, 81, 79, 78.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good season"], forecast: "Abundant" }},
  { id: 20, name: "Ampalaya 4-5 pcs/kg", category: "vegetables", currentPrice: 126.30, averagePrice: 130, unit: "kg", location: "NCR", icon: "🥒", status: "STABLE", savings: 3.70, trend: [133, 132, 131, 129, 127, 126.30], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Regular supply"], forecast: "Normal" }},
  { id: 21, name: "Squash (Kalabasa)", category: "vegetables", currentPrice: 42.50, averagePrice: 48, unit: "kg", location: "NCR", icon: "🎃", status: "MURA", savings: 5.50, trend: [52, 50, 49, 46, 44, 42.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Peak season"], forecast: "Plentiful" }},
  { id: 22, name: "Sayote (Medium)", category: "vegetables", currentPrice: 68.40, averagePrice: 72, unit: "kg", location: "NCR", icon: "🥒", status: "MURA", savings: 3.60, trend: [75, 74, 73, 71, 69, 68.40], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good harvest"], forecast: "Stable" }},
  { id: 23, name: "Chayote (Medium 301-450)", category: "vegetables", currentPrice: 78.50, averagePrice: 82, unit: "kg", location: "NCR", icon: "🥒", status: "MURA", savings: 3.50, trend: [85, 84, 83, 81, 79, 78.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal conditions"], forecast: "Good supply" }},
  { id: 24, name: "Celery (Medium 501-800)", category: "vegetables", currentPrice: 156.84, averagePrice: 162, unit: "kg", location: "NCR", icon: "🌿", status: "STABLE", savings: 5.16, trend: [168, 166, 164, 161, 158, 156.84], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Steady production"], forecast: "Stable" }},
  { id: 25, name: "Corn (White)", category: "vegetables", currentPrice: 85.20, averagePrice: 88, unit: "kg", location: "NCR", icon: "🌽", status: "MURA", savings: 2.80, trend: [92, 90, 89, 87, 86, 85.20], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good yield"], forecast: "Plentiful" }},
  
  // VEGETABLES - Root crops & Tubers
  { id: 26, name: "Potato (Local 10-12)", category: "vegetables", currentPrice: 111.70, averagePrice: 115, unit: "kg", location: "NCR", icon: "🥔", status: "STABLE", savings: 3.30, trend: [118, 117, 116, 114, 112, 111.70], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal conditions"], forecast: "Stable" }},
  { id: 27, name: "Carrots (Medium)", category: "vegetables", currentPrice: 95.30, averagePrice: 98, unit: "kg", location: "NCR", icon: "🥕", status: "MURA", savings: 2.70, trend: [102, 100, 99, 97, 96, 95.30], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good season"], forecast: "Steady" }},
  { id: 28, name: "Ginger", category: "vegetables", currentPrice: 145.60, averagePrice: 152, unit: "kg", location: "NCR", icon: "🫚", status: "MURA", savings: 6.40, trend: [158, 156, 153, 150, 147, 145.60], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Regular harvest"], forecast: "Stable" }},
  
  // RICE varieties
  { id: 29, name: "Glutinous Rice", category: "rice", currentPrice: 61.19, averagePrice: 68, unit: "kg", location: "NCR", icon: "🍚", status: "MURA", savings: 6.81, trend: [72, 70, 68, 65, 63, 61.19], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Good harvest season", "Low drought risk"], forecast: "Stable supply expected" }},
  { id: 30, name: "Premium Rice (5% broken)", category: "rice", currentPrice: 57.49, averagePrice: 55, unit: "kg", location: "NCR", icon: "🍚", status: "STABLE", savings: -2.49, trend: [53, 54, 55, 56, 57, 57.49], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Demand stable"], forecast: "Normal range" }},
  { id: 31, name: "Regular Milled Rice", category: "rice", currentPrice: 48.50, averagePrice: 50, unit: "kg", location: "NCR", icon: "🍚", status: "MURA", savings: 1.50, trend: [52, 51, 50, 49, 48.5, 48.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Adequate supply"], forecast: "Stable" }},
  { id: 32, name: "Well Milled Rice", category: "rice", currentPrice: 52.30, averagePrice: 54, unit: "kg", location: "NCR", icon: "🍚", status: "MURA", savings: 1.70, trend: [56, 55, 54, 53, 52.5, 52.30], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good production"], forecast: "Steady" }},
  
  // POULTRY
  { id: 33, name: "Chicken (Whole)", category: "poultry", currentPrice: 165.50, averagePrice: 172, unit: "kg", location: "NCR", icon: "🍗", status: "STABLE", savings: 6.50, trend: [175, 173, 171, 169, 167, 165.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Heat stress concerns", "Feed costs stable"], forecast: "Monitoring temperature impact" }},
  { id: 34, name: "Chicken Breast", category: "poultry", currentPrice: 215.00, averagePrice: 220, unit: "kg", location: "NCR", icon: "🍗", status: "MURA", savings: 5.00, trend: [225, 223, 221, 218, 216, 215.00], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Supply adequate"], forecast: "Stable" }},
  { id: 35, name: "Chicken Leg", category: "poultry", currentPrice: 185.00, averagePrice: 190, unit: "kg", location: "NCR", icon: "🍗", status: "MURA", savings: 5.00, trend: [195, 193, 191, 188, 186, 185.00], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good supply"], forecast: "Normal" }},
  { id: 36, name: "Eggs (Medium)", category: "poultry", currentPrice: 6.85, averagePrice: 7.20, unit: "piece", location: "NCR", icon: "🥚", status: "MURA", savings: 0.35, trend: [7.5, 7.3, 7.2, 7.0, 6.9, 6.85], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Stable production"], forecast: "Good supply" }},
  { id: 37, name: "Eggs (Large)", category: "poultry", currentPrice: 7.50, averagePrice: 7.80, unit: "piece", location: "NCR", icon: "🥚", status: "MURA", savings: 0.30, trend: [8.2, 8.0, 7.9, 7.7, 7.6, 7.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Steady production"], forecast: "Plentiful" }},
  
  // MEAT - Pork
  { id: 38, name: "Pork Kasim", category: "meat", currentPrice: 285, averagePrice: 295, unit: "kg", location: "NCR", icon: "🥩", status: "STABLE", savings: 10, trend: [300, 298, 295, 290, 287, 285], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Rising temperatures affecting livestock"], forecast: "Price may increase if heat persists" }},
  { id: 39, name: "Pork Liempo", category: "meat", currentPrice: 310, averagePrice: 320, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [328, 325, 322, 318, 314, 310], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Heat affecting supply"], forecast: "Monitoring closely" }},
  { id: 40, name: "Pork Pigue", category: "meat", currentPrice: 295, averagePrice: 305, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [312, 310, 308, 302, 298, 295], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Supply adequate"], forecast: "Stable" }},
  { id: 41, name: "Pork Offals (Local)", category: "meat", currentPrice: 185, averagePrice: 195, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [202, 200, 198, 192, 188, 185], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good supply"], forecast: "Normal" }},
  
  // MEAT - Beef
  { id: 42, name: "Beef Brisket", category: "meat", currentPrice: 420, averagePrice: 435, unit: "kg", location: "NCR", icon: "🥩", status: "STABLE", savings: 15, trend: [445, 442, 438, 432, 426, 420], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "high", factors: ["Drought affecting feed supply"], forecast: "Watch for potential increases" }},
  { id: 43, name: "Beef Ribs", category: "meat", currentPrice: 385, averagePrice: 395, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [405, 402, 398, 392, 388, 385], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "high", factors: ["Feed costs rising"], forecast: "Upward pressure" }},
  { id: 44, name: "Beef Shank", category: "meat", currentPrice: 365, averagePrice: 375, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [382, 380, 378, 372, 368, 365], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Supply moderate"], forecast: "Stable" }},
  { id: 45, name: "Carabao Beef", category: "meat", currentPrice: 295, averagePrice: 305, unit: "kg", location: "NCR", icon: "🥩", status: "MURA", savings: 10, trend: [315, 312, 308, 302, 298, 295], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Local production stable"], forecast: "Normal" }},
  
  // FISH - Fresh
  { id: 46, name: "Tilapia", category: "fish", currentPrice: 135, averagePrice: 145, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [152, 150, 147, 142, 138, 135], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good water quality"], forecast: "Stable aquaculture output" }},
  { id: 47, name: "Bangus (Milkfish)", category: "fish", currentPrice: 158, averagePrice: 168, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [175, 172, 168, 164, 161, 158], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Calm seas", "Good fishing conditions"], forecast: "Supply stable" }},
  { id: 48, name: "Galunggong (Small)", category: "fish", currentPrice: 185, averagePrice: 195, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [205, 202, 198, 192, 188, 185], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good catch"], forecast: "Plentiful" }},
  { id: 49, name: "Galunggong (Medium)", category: "fish", currentPrice: 205, averagePrice: 215, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [225, 222, 218, 212, 208, 205], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Weather favorable"], forecast: "Good supply" }},
  { id: 50, name: "Alumahan", category: "fish", currentPrice: 275, averagePrice: 285, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [295, 292, 288, 282, 278, 275], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good fishing season"], forecast: "Abundant" }},
  { id: 51, name: "Dalagang Bukid", category: "fish", currentPrice: 265, averagePrice: 275, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [285, 282, 278, 272, 268, 265], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Waters calm"], forecast: "Steady catch" }},
  { id: 52, name: "Tulingan", category: "fish", currentPrice: 245, averagePrice: 255, unit: "kg", location: "NCR", icon: "🐟", status: "MURA", savings: 10, trend: [265, 262, 258, 252, 248, 245], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Normal season"], forecast: "Good availability" }},
  
  // SPICES
  { id: 53, name: "Garlic (Local)", category: "spices", currentPrice: 185, averagePrice: 165, unit: "kg", location: "NCR", icon: "🧄", status: "MAHAL", savings: -20, trend: [160, 165, 170, 175, 180, 185], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "high", factors: ["Drought reducing yield", "Heat damage"], forecast: "Limited supply, prices rising" }},
  { id: 54, name: "Garlic (Imported)", category: "spices", currentPrice: 155, averagePrice: 145, unit: "kg", location: "NCR", icon: "🧄", status: "MAHAL", savings: -10, trend: [140, 142, 145, 148, 152, 155], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Global supply tight"], forecast: "Price pressure" }},
  { id: 55, name: "Ginger (Native)", category: "spices", currentPrice: 125, averagePrice: 135, unit: "kg", location: "NCR", icon: "🫚", status: "MURA", savings: 10, trend: [145, 142, 138, 132, 128, 125], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Good harvest"], forecast: "Abundant" }},
  { id: 56, name: "Salt (Iodized)", category: "spices", currentPrice: 38.73, averagePrice: 40, unit: "kg", location: "NCR", icon: "🧂", status: "STABLE", savings: 1.27, trend: [42, 41, 40, 39.5, 39, 38.73], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Production normal"], forecast: "Stable" }},
  
  // FUEL
  { id: 57, name: "Diesel", category: "fuel", currentPrice: 58.75, averagePrice: 62, unit: "L", location: "NCR", icon: "⛽", status: "STABLE", savings: 3.25, trend: [64, 63, 61.5, 60, 59, 58.75], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Global climate policies", "Renewable shift"], forecast: "Long-term downward pressure" }},
  { id: 58, name: "Gasoline 91", category: "fuel", currentPrice: 62.50, averagePrice: 65, unit: "L", location: "NCR", icon: "⛽", status: "STABLE", savings: 2.50, trend: [67, 66, 65, 64, 63, 62.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Carbon pricing"], forecast: "Gradual decrease" }},
  { id: 59, name: "Gasoline 95", category: "fuel", currentPrice: 64.20, averagePrice: 67, unit: "L", location: "NCR", icon: "⛽", status: "STABLE", savings: 2.80, trend: [69, 68, 67, 66, 65, 64.20], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Climate policies impact"], forecast: "Declining trend" }},
  { id: 60, name: "Gasoline 97", category: "fuel", currentPrice: 66.80, averagePrice: 69, unit: "L", location: "NCR", icon: "⛽", status: "STABLE", savings: 2.20, trend: [71, 70, 69, 68, 67, 66.80], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "medium", factors: ["Market adjusting"], forecast: "Downward trajectory" }},
  { id: 61, name: "Kerosene", category: "fuel", currentPrice: 55.30, averagePrice: 58, unit: "L", location: "NCR", icon: "⛽", status: "MURA", savings: 2.70, trend: [60, 59, 58, 57, 56, 55.30], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Demand declining"], forecast: "Stable" }},
  { id: 62, name: "LPG", category: "fuel", currentPrice: 68.50, averagePrice: 72, unit: "kg", location: "NCR", icon: "⛽", status: "MURA", savings: 3.50, trend: [75, 74, 73, 71, 69, 68.50], lastUpdated: "2026-02-27T07:00:00Z", climateImpact: { level: "low", factors: ["Supply adequate"], forecast: "Normal" }}
];

// Climate metrics as additional monitoring data
export const climateMetrics = [
  {
    id: 'c1',
    name: "Temperature",
    category: "climate",
    currentValue: 28.5,
    averageValue: 31.2,
    unit: "°C",
    status: "GOOD",
    icon: "🌡️",
    trend: [32, 31, 30, 29.5, 29, 28.5],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Comfortable temperature range. Stay hydrated and use sun protection.",
    impact: "Lower temperatures benefit crop growth and reduce livestock heat stress"
  },
  {
    id: 'c2',
    name: "Rainfall",
    category: "climate",
    currentValue: 45.3,
    averageValue: 35.8,
    unit: "mm",
    status: "GOOD",
    icon: "🌧️",
    trend: [28, 32, 38, 42, 44, 45.3],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Adequate rainfall for agriculture. Good conditions for farming.",
    impact: "Optimal moisture levels supporting vegetable production and lowering irrigation costs"
  },
  {
    id: 'c3',
    name: "Air Quality Index",
    category: "climate",
    currentValue: 42,
    averageValue: 68,
    unit: "AQI",
    status: "GOOD",
    icon: "🌬️",
    trend: [65, 58, 52, 48, 45, 42],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Air quality is excellent. Perfect conditions for outdoor activities.",
    impact: "Good air quality supports healthy crop growth and livestock wellness"
  },
  {
    id: 'c4',
    name: "Humidity",
    category: "climate",
    currentValue: 72,
    averageValue: 65,
    unit: "%",
    status: "MODERATE",
    icon: "💧",
    trend: [68, 69, 70, 71, 71.5, 72],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Slightly elevated humidity. Monitor for pest issues in crops.",
    impact: "Higher humidity may increase disease pressure on leafy vegetables"
  },
  {
    id: 'c5',
    name: "UV Index",
    category: "climate",
    currentValue: 9.2,
    averageValue: 7.5,
    unit: "UV",
    status: "WARNING",
    icon: "☀️",
    trend: [6.5, 7, 7.8, 8.5, 9, 9.2],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Very high UV levels. Use SPF 50+ sunscreen and seek shade during 10am-4pm.",
    impact: "High UV can stress crops but also helps natural pest control"
  },
  {
    id: 'c6',
    name: "Soil Moisture",
    category: "climate",
    currentValue: 35,
    averageValue: 28,
    unit: "%",
    status: "GOOD",
    icon: "🌱",
    trend: [25, 27, 29, 31, 33, 35],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Optimal soil moisture for planting. Good conditions for crop growth.",
    impact: "Excellent conditions supporting vegetable production and stable prices"
  },
  {
    id: 'c7',
    name: "Wind Speed",
    category: "climate",
    currentValue: 15.3,
    averageValue: 18.7,
    unit: "km/h",
    status: "GOOD",
    icon: "💨",
    trend: [22, 20, 18.5, 17, 16, 15.3],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Gentle breeze conditions. Safe for all outdoor activities.",
    impact: "Calm conditions favorable for farming operations and fishing"
  },
  {
    id: 'c8',
    name: "Drought Index",
    category: "climate",
    currentValue: 2.1,
    averageValue: 3.5,
    unit: "scale",
    status: "GOOD",
    icon: "🏜️",
    trend: [4.2, 3.8, 3.2, 2.8, 2.4, 2.1],
    lastUpdated: "2026-02-27T07:00:00Z",
    recommendation: "Low drought risk. Adequate water supply for agriculture.",
    impact: "Minimal drought stress keeping crop prices stable"
  }
];

export const bestDeals = marketItems
  .filter(item => item.status === "MURA")
  .sort((a, b) => b.savings - a.savings)
  .slice(0, 8);

export const categories = [
  { id: 'all', name: 'All Items', icon: '📊' },
  { id: 'vegetables', name: 'Vegetables', icon: '🥬' },
  { id: 'meat', name: 'Meat', icon: '🥩' },
  { id: 'poultry', name: 'Poultry', icon: '🍗' },
  { id: 'fish', name: 'Fish', icon: '🐟' },
  { id: 'rice', name: 'Rice', icon: '🍚' },
  { id: 'spices', name: 'Spices', icon: '🌶️' },
  { id: 'fuel', name: 'Fuel', icon: '⛽' },
  { id: 'climate', name: 'Climate Data', icon: '🌡️' }
];
