// =======================================================
// Campus Demand Intelligence & Order Batching Frontend Client
// =======================================================

window.campusIntelligence = {
    async fetchDemandInsights() {
        const res = await window.apiFetch("/api/intelligence/demand-insights");
        if (res.success && res.data) {
            return res.data;
        }
        // Fallback for offline dev
        return {
            total_historical_orders: 48,
            total_revenue: 14850.0,
            predicted_high_demand: [
                {
                    product_name: "Maggi 2-Minute Masala Noodles (4-Pack)",
                    building_name: "Hostel Block B (Boys Hostel)",
                    time_window: "8:30 PM - 10:30 PM (Late Night)",
                    current_stock: 14,
                    predicted_demand: 38,
                    recommended_stock: 45,
                    demand_multiplier: 2.7,
                    risk_level: "HIGH",
                    confidence: 0.94,
                    insight: "Maggi demand is predicted to increase ~2.7x between 8:30 PM and 10:30 PM in Hostel Block B."
                },
                {
                    product_name: "Red Bull Energy Drink (Can)",
                    building_name: "Ramanujan Hostel",
                    time_window: "10:00 PM - 1:00 AM (Exam Peak)",
                    current_stock: 8,
                    predicted_demand: 26,
                    recommended_stock: 30,
                    demand_multiplier: 3.25,
                    risk_level: "CRITICAL",
                    confidence: 0.91,
                    insight: "Energy drinks are experiencing severe stock depletion risk prior to midnight exam review."
                },
                {
                    product_name: "Special Deluxe Paneer Butter Masala Thali",
                    building_name: "Main Canteen Counter 2",
                    time_window: "1:00 PM - 2:30 PM (Lunch Rush)",
                    current_stock: 25,
                    predicted_demand: 42,
                    recommended_stock: 50,
                    demand_multiplier: 1.68,
                    risk_level: "MODERATE",
                    confidence: 0.88,
                    insight: "Paneer Thali meal rush expected at Main Canteen Counter 2 during afternoon break."
                }
            ],
            hostel_demand_distribution: {
                "Hostel Block B": 28,
                "Ramanujan Hostel": 19,
                "Aryabhatta Hostel": 14,
                "CSE Dept Labs": 9
            }
        };
    },

    async fetchDeliveryBatches() {
        const res = await window.apiFetch("/api/intelligence/delivery-batches");
        if (res.success && res.data) {
            return res.data;
        }
        return [
            {
                batch_id: "BATCH-RUNNER-101",
                building_name: "Hostel Block B (Boys Hostel)",
                orders_count: 4,
                rooms_covered: ["Room 104", "Room 212", "Room 305", "Room 318"],
                total_batch_value: 680.0,
                runner_assigned: "Campus Runner #1 (Hostel Express)",
                estimated_departure: "Departing in 4 mins",
                savings_summary: "Grouped 4 orders into 1 single runner trip to Hostel Block B (saved 36 mins runner time).",
                orders: [
                    { order_number: "ORD-B82A1C01", room_number: "Room 104", total: 180.0, status: "CONFIRMED" },
                    { order_number: "ORD-C94F32D2", room_number: "Room 212", total: 140.0, status: "PREPARING" },
                    { order_number: "ORD-E11A9903", room_number: "Room 305", total: 210.0, status: "CONFIRMED" },
                    { order_number: "ORD-F77B02D4", room_number: "Room 318", total: 150.0, status: "PLACED" }
                ]
            },
            {
                batch_id: "BATCH-RUNNER-102",
                building_name: "Ramanujan Hostel",
                orders_count: 3,
                rooms_covered: ["Room 101", "Room 108", "Room 204"],
                total_batch_value: 490.0,
                runner_assigned: "Campus Runner #2",
                estimated_departure: "Departing in 9 mins",
                savings_summary: "Grouped 3 orders into 1 single runner trip to Ramanujan Hostel (saved 24 mins runner time).",
                orders: [
                    { order_number: "ORD-A102BB91", room_number: "Room 101", total: 250.0, status: "CONFIRMED" },
                    { order_number: "ORD-D304EE88", room_number: "Room 108", total: 120.0, status: "PLACED" },
                    { order_number: "ORD-K889FF21", room_number: "Room 204", total: 120.0, status: "PREPARING" }
                ]
            }
        ];
    }
};
