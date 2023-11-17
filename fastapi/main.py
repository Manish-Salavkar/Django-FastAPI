
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from datetime import date
from pydantic import BaseModel
from typing import List


DB_CONFIG = {
    'user':'user',
    'port':'port',
    'database':'database',
    'password':'password',
    'host':'localhost'
}

app = FastAPI()

origins = [
    "http://127.0.0.1:9000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
    


@app.get("/get_data/{query_type}")
async def get_data(query_type: str, 
                   fccid: str = Query(None, description="fccid"),
                   user_id: int = Query(None, description="user_id"),
                   unique_key: str = Query(None, description="unique_key")
                   ):

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        today = date.today().isoformat()


        if query_type == "detailed":
            if fccid is None:
                return JSONResponse(content={"error":"No fccid provided"})
            cursor.execute("SELECT * FROM scraped_data WHERE fccid = %s", (fccid,))

        elif query_type == "all":
            cursor.execute("SELECT * FROM scraped_data")
        
        elif query_type == "daily":
            cursor.execute("SELECT * FROM scraped_data WHERE date_scraped = %s", (today,))



        else:
            return JSONResponse(content={"error": "invalid Query"})
        
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        if not data:
            return JSONResponse(content={"message": "No data found"})
        
        if query_type == "detailed" or query_type == "all" or query_type == "daily" :
            data_list = [
                {
                    "fccid": row[0],
                    "date": str(row[1]),
                    "job_title": row[2],
                    "company_name": row[3],
                    "company_location": row[4],
                    "salary": row[5],
                    "url": row[6],
                    "job_description": row[7]
                }
                for row in data
            ]
        else:
            return JSONResponse(content={"message": "Invalid Query"})

        return JSONResponse(content=data_list)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



class UserProfileData(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    unique_key: str

@app.post("/save_user_profile")
async def save_user_profile(user_profile: UserProfileData):
    try:

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO user_profile (user_id, first_name, last_name, unique_key) VALUES (%s, %s, %s, %s)",
            (user_profile.user_id, user_profile.first_name, user_profile.last_name, user_profile.unique_key),
        )


        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "User profile data saved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



class BookmarkData(BaseModel):
    user_id: int
    unique_key: str
    fccid: str

@app.post("/save_bookmark")
async def save_bookmark(bookmark: BookmarkData):
    try:

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_profile WHERE user_id = %s AND unique_key = %s",
            (bookmark.user_id, bookmark.unique_key),
        )

        user_profile = cursor.fetchone()

        if user_profile is not None:
            existing_fccid = user_profile[4]

            if existing_fccid:
                new_fccid = f"{existing_fccid}, {bookmark.fccid}"
            else:
                new_fccid = bookmark.fccid

            cursor.execute(
                "UPDATE user_profile SET fccid = %s WHERE unique_key = %s AND user_id = %s",
                (new_fccid, bookmark.unique_key, bookmark.user_id),
            )

            conn.commit()

            cursor.close()
            conn.close()

            return {"message": "Bookmark added successfully"}
        
        else:
            return {"message": "User not found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.get("/get_user_bookmark")
async def get_user_bookmark(user_id: int = Query(..., description="user_id"), unique_key: str = Query(..., description="unique_key")):

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT fccid FROM user_profile WHERE user_id = %s AND unique_key = %s",
            (user_id, unique_key),
        )

        user_profile = cursor.fetchone()

        if user_profile is not None:

            bookmarked_fccids = [fccid.strip() for fccid in user_profile[0].split(",") if fccid]

            print(bookmarked_fccids)

            cursor.execute(
                "SELECT * FROM scraped_data WHERE fccid IN %s",
                (tuple(bookmarked_fccids),),
            )

            data = cursor.fetchall()

            print(bookmarked_fccids)

            cursor.close()
            conn.close()

            data_list = [
                {
                    "fccid": row[0],
                    "date": str(row[1]),
                    "job_title": row[2],
                    "company_name": row[3],
                    "company_location": row[4],
                    "salary": row[5],
                    "url": row[6],
                    "job_description": row[7]       
                }
                for row in data
            ]

            print(data_list)

            return {"bookmarked_data": data_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"bookmarked_data": []}



class RemoveBookmark(BaseModel):
    user_id: int
    unique_key: str
    fccid: str

@app.post("/remove_bookmark")
async def remove_bookmark(rem_bookmark: RemoveBookmark):
    try:

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_profile WHERE user_id = %s AND unique_key = %s",
            (rem_bookmark.user_id, rem_bookmark.unique_key),
        )

        user_profile = cursor.fetchone()

        if user_profile is not None:
            existing_fccids = user_profile[0]
            if existing_fccids:
                existing_fccid_list = [fccid.strip() for fccid in existing_fccids.split(",") if fccid]
                if rem_bookmark.fccid in existing_fccid_list:
                    existing_fccid_list.remove(rem_bookmark.fccid)
                    updated_fccids = ', '.join(existing_fccid_list)
                    cursor.execute(
                        "UPDATE user_profile SET fccid = %s WHERE user_id = %s AND unique_key = %s",
                        (updated_fccids, rem_bookmark.user_id, rem_bookmark.unique_key),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return {"message": "Bookmark removed successfully"}
                else:
                    cursor.close()
                    conn.close()
                    raise HTTPException(status_code=400, detail="FCCID not found in user's bookmarks")
            else:
                cursor.close()
                conn.close()
                raise HTTPException(status_code=400, detail="No bookmarks found for the user")
        else:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))