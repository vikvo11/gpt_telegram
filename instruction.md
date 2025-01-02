1. POST /costs/year
   Purpose: Retrieve all expense records for a specified year.
   Description: Accepts a JSON body with "year". Returns a list of expenses (e.g., rent, groceries) for the given year.

   Example Usage:
   curl -X POST -H "Content-Type: application/json" -d '{"year": "2025"}' https://vorovik.pythonanywhere.com/api/costs/year

   Request Body:
   {
     "year": "2025"
   }

   Sample Response:
   [
     {
       "id": 1,
       "title": "Rent",
       "cost": 700,
       "year": "2025",
       "month": "01",
       "limits": null
     },
     ...
   ]

2. POST /costs/month
   Purpose: Retrieve all expense records for a specific year and month.
   Description: Accepts a JSON body with "year" and "month". Returns a list of matching expenses for the specified year/month.

   Example Usage:
   curl -X POST -H "Content-Type: application/json" -d '{"year":"2025", "month":"01"}' https://vorovik.pythonanywhere.com/api/costs/month

   Request Body:
   {
     "year": "2025",
     "month": "01"
   }

   Sample Response:
   [
     {
       "id": 10,
       "title": "Utilities",
       "cost": 120,
       "year": "2025",
       "month": "01",
       "limits": null
     },
     ...
   ]

3. GET /limits
   Purpose: Fetch all limit records, including the "overall" limit.
   Description: Returns an array of limits, each containing a "title" and "limit_value".

   Example Usage:
   curl -X GET https://vorovik.pythonanywhere.com/api/limits

   Sample Response:
   [
     {
       "id": 1,
       "title": "Groceries",
       "limit_value": 3000
     },
     {
       "id": 2,
       "title": "overall",
       "limit_value": 10000
     },
     ...
   ]

4. POST /limits
   Purpose: Add or update a limit (e.g., "Rent," "Groceries," or "overall").
   Description: Accepts JSON with "title" and "limit_value". Adjusts "overall" if it is lower than the sum of other limits. Returns the updated list of limits.

   Example Usage:
   curl -X POST -H "Content-Type: application/json" -d '{"title":"Groceries","limit_value":5000}' https://vorovik.pythonanywhere.com/api/limits

   Request Body:
   {
     "title": "Groceries",
     "limit_value": 5000
   }

   Sample Response:
   [
     {
       "id": 1,
       "title": "Groceries",
       "limit_value": 5000
     },
     {
       "id": 2,
       "title": "overall",
       "limit_value": 10000
     },
     ...
   ]