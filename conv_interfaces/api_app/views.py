from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import json
from django.http import JsonResponse

api_key = "5847175a9655f0710888e21f2f7b9558"

genre_list = f'https://api.themoviedb.org/3/genre/movie/list?language=en&api_key={api_key}'
genres= requests.get(genre_list)
genre_list = json.loads(genres.text)['genres']

genre_dict = {}
for each in genre_list:
    genre_dict[each['name'].lower()] = each['id']

current_recs = []
where_in_rec_list = 0
current_movie_id = ""

current_director = ""
current_actor = ""
current_genre = ""

@api_view(['GET'])
def getMovieRecommendations(request, otherparam, director, actor, genre):
    global current_movie_id
    global where_in_rec_list
    global current_recs

    global current_director
    global current_actor
    global current_genre

    api_query = f'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&api_key={api_key}'

    #if director != current_director or actor != current_actor or genre != current_genre:
    original_info = actor + " " + director + " " + genre 
    print([director, actor, genre])

    if genre != "$session.params.genre" and genre != "null" and genre != "dontcare":
        genre = genre_dict[genre.lower()]
        api_query = api_query + f"&with_genres={genre}"

    if director != "$session.params.director" and director != "null" and director != "dontcare":
        director = get_person_id(director)
        api_query = api_query + f"&with_crew={director}"

    if actor != "$session.params.starring" and actor != "null" and actor != "dontcare":
        actor = get_person_id(actor)
        api_query = api_query + f"&with_cast={actor}"

    if director != current_director or actor != current_actor or genre != current_genre:    
        r = requests.get(api_query)
        current_recs = json.loads(r.text)['results']
        where_in_rec_list = 0

        current_director = director
        current_actor = actor
        current_genre = genre
    else:
        #if no extra params are added we want to movie one forward in the rec list
        where_in_rec_list = where_in_rec_list + 1
        if where_in_rec_list >= len(current_recs) -1:
            where_in_rec_list = 0

    if current_recs == []:
         return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"aggregate_rating": "None", "title": "None", "num_movies": "None"}}]}})

        #return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": ["No movies matching those details were found "+ original_info]}}]}})
    
    #movie_details = f"I've found {len(current_recs)} movies for you. How does {current_recs[where_in_rec_list]['title']} sound? It has a rating of {round(current_recs[where_in_rec_list]['vote_average'],2)}."
    current_movie_id = current_recs[where_in_rec_list]['id']
    genres = get_genre_details()
    lead_actors, director = get_credits()
    genre_list = []
    for genre in genres:
        genre_list.append(genre["name"])
    
    return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"aggregate_rating": round(current_recs[where_in_rec_list]['vote_average'],2), "title":current_recs[where_in_rec_list]['title'], "num_movies": len(current_recs)}}]}})

def get_person_id(person_query):
    # find the person ID in the movie API so that we can query movies with that person
    api_query = f'https://api.themoviedb.org/3/search/person?api_key={api_key}&language=en-US&query={person_query}'
    
    r = requests.get(api_query)
    results = json.loads(r.text)['results']
    if results == []:
        return None
    return results[0]['id']

@api_view(['GET'])
def getMovieInformation(request, otherparam, requestInfo):
    requestInfo = requestInfo.strip('][').split(', ')
    genres = get_genre_details()
    lead_actors, director = get_credits()
    genre_list = []
    for genre in genres:
        genre_list.append(genre["name"])

    if len(requestInfo) == 1:
        if "genre" in requestInfo:
            if len(genre_list) > 1:
               return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": [" and ".join(genre_list)]}}]}})
            else:
                return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": [genre_list[0]]}}]}})
        if "directors" in requestInfo:
            return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": ['It was directed by ' + director]}}]}})
        if "starring" in requestInfo:
            if len(lead_actors) > 1:
                return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": ['It stars ' + " and ".join(lead_actors)]}}]}})
            else:
                return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": ['It stars ' + lead_actors[0]]}}]}})

    response = "It is"
    if "genre" in requestInfo:
            if len(genre_list) > 1:
                response = response + " a " + " and ".join(genre_list) + " movie,"
            else:
                response = response + "a" + genre_list[0] + " movie,"
    if "directors" in requestInfo:
            response = response + " directed by " + director
    if "starring" in requestInfo:
            if len(lead_actors) > 1:
                 response = response + ", starring " +  " and ".join(lead_actors)
            else:
                response = response + ", starring " + lead_actors[0]

    return JsonResponse({"fulfillmentResponse": {"messages": [{"text": {"text": [response]}}]}})       

def get_genre_details():
    detail_query = f"https://api.themoviedb.org/3/movie/{current_movie_id}?api_key={api_key}&language=en-US"
    r = requests.get(detail_query)
    results = json.loads(r.text)["genres"]
    return results


def get_credits():
    # get movie credits details for cast and crew information
    detail_query = f"https://api.themoviedb.org/3/movie/{current_movie_id}/credits?api_key={api_key}&language=en-US"
    
    r = requests.get(detail_query)
    lead_actors = get_actor_names(json.loads(r.text)["cast"][:2])
    crew = json.loads(r.text)["crew"]
    directors = get_directors(crew)
    return lead_actors, directors

def get_directors(crew):
    directors = []
    for member in crew:
        if (member['job'] == 'Director' or member['known_for_department'] == 'Directing') and member['name'] not in directors:
            directors.append(member["name"])

    #only return first director
    return directors[0]

def get_actor_names(actors):
    actor_names = []
    for actor in actors:
        actor_names.append(actor['name'])
        print("ACTOR NAMES?")
    return actor_names

