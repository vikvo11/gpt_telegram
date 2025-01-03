Currency = CZK add this info for numbers.
Always use all data from queries as it is important for accurate calculations. Re-query data to be more accurate
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

5. POST /costs/range
   Purpose: Retrieve expense records across a range of months and years.
   Description: Accepts JSON with "start_year", "start_month", "end_year", and "end_month". If "start_month" or "end_month" is missing, defaults to "01" or "12" respectively. Returns all records from [start_year start_month] through [end_year end_month] (inclusive).

   Example Usage:
   curl -X POST -H "Content-Type: application/json" -d '{"start_year": "2024", "start_month": "03", "end_year": "2025", "end_month": "05"}' https://vorovik.pythonanywhere.com/api/costs/range

   Request Body:
   {
     "start_year": "2024",
     "start_month": "03",
     "end_year": "2025",
     "end_month": "05"
   }

   Sample Response:
   [
     {
       "id": 25,
       "title": "Rent",
       "cost": 750,
       "year": "2024",
       "month": "03",
       "limits": null
     },
     {
       "id": 30,
       "title": "Entertainment",
       "cost": 120,
       "year": "2025",
       "month": "04",
       "limits": null
     },
     ...
   ]

6. DELETE /limits/{title}
   Purpose: Remove a specific limit entry from the limit_dict table.
   Constraints: The "общий" limit cannot be deleted; attempting to do so returns an error.

   Status Codes:
   - 200: Successfully removed the limit (returns updated list of limits).
   - 403: Attempt to delete the "общий" limit.
   - 404: Specified limit not found.

   Example Usage:
   curl -X DELETE -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" "https://vorovik.pythonanywhere.com/api/limits/Groceries"

   Request: A simple DELETE request with your API Key in the header.

   Sample Response (200 OK):
   [
     {
       "id": 2,
       "title": "Rent",
       "limit_value": 8000
     },
     {
       "id": 3,
       "title": "общий",
       "limit_value": 12000
     }
   ]

   If the "Groceries" limit did not exist, you would receive:
   {
     "error": "Limit 'Groceries' not found"
   } (HTTP 404)

   If you tried to delete "общий", you would receive:
   {
     "error": "Cannot delete the main 'общий' limit"
   } (HTTP 403)