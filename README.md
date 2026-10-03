[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm_Noncommercial_1.0.0-red.svg)](##license--legal-disclaimer)

# EDSea PLUR Planner

> Your ultimate festival-at-sea companion and itinerary coordinator! Plan sets, coordinate meetups, and embrace PLUR (Peace, Love, Unity, Respect) while sailing on the electric ocean.

---

## Features

- **Festival & Set Scheduler:** Keep track of your favorite artists, stage locations, and set times so you never miss a beat.
- **Build Recommendations:** The EDSea PLUR Planner generates recommendations based on a few selections to help fill your schedule.
- **Add Activities:** Complete your week with brunch, yoga, gameshows, and more.
- **Responsive & Portable:** Designed to be lightweight and responsive.  Once your schedule is the way you want it, download it so you can keep it with you even without internet or cell signal.

---

## Tech Stack

- **Frontend:** React / Next.js / TailwindCSS
- **Backend:** Python / FastAPI / PostgreSQL / Google OR Tools
- **Hosting / Deployment:** Docker / TBD

---

## Getting Started

Follow these instructions to get a local copy up and running for development and testing purposes.

### Prerequisites

Check [requirements.txt](https://github.com/brosenlieb/EDSea_PLUR_Planner/blob/main/backend/app/requirements.txt) to know what installs are needed.  

You'll also need Docker for the containerized version of PostgreSQL, and you may want pgAdmin or a similar client to directly view DB tables.

## Install & Setup

1. **Clone the repository:**
   
   `git clone https://github.com/brosenlieb/EDSea_PLUR_Planner.git`
2. **Navigate to the project directory**

   `cd EDSea_PLUR_Planner`
3.  **Install Dependencies**

    `npm install`
4.  **Environement**

    Copy `.env.example` to your root directory and replace with your own relevant values
5.  **Run the app**

    Use `uvicorn` and `npm` to launch the server, then navigate to `http://localhost:3000`

## Contributing

Contributions, issues, and feature requests are welcome!
Feel free to utilize the [Issues](https://github.com/brosenlieb/EDSea_PLUR_Planner/issues) page.

1. Fork the Project
2. Create your Feature Branch `git checkout -b feature/AmazingFeature`
3. Commit your Changes `git commit -m 'Add some AmazingFeature'`
4. Push to the Branch `git push origin feature/AmazingFeature`
5. Open a Pull Request

Submitted code should be well-formatted, type-casted, appropriately commented, and follow modern Python standards.  Include unit and integration tests where applicable with pytest.

## License & Legal Disclaimer

This project is source-available under the **PolyForm Noncommercial License 1.0.0**. 

By using, copying, or modifying this software, you agree to the following strict conditions:

1. **Strictly Non-Commercial:** This software is free strictly for personal, educational, or hobby use. Use by corporations, businesses, or individuals for commercial advantage or monetary compensation is strictly prohibited.
2. **Mandatory Attribution:** If you reuse, modify, or redistribute any part of this source code, you **must give prominent credit** to the original author by including a link back to this GitHub repository.
3. **No Warranty:** This hobby project is provided "as-is" without any warranty of any kind. 
