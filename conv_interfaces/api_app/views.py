from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import json

#from serializers import GroupSerializer, UserSerializer

api_key = "5847175a9655f0710888e21f2f7b9558"

genre_list = f'https://api.themoviedb.org/3/genre/movie/list?language=en&api_key={api_key}'
genres= requests.get(genre_list)
genre_list = json.loads(genres.text)['genres']

genre_dict = {}
for each in genre_list:
    genre_dict[each['name'].lower()] = each['id']


#pass in movie id to get info!

@api_view(['GET'])
def getMovieRecommendations(request, otherparam, director, actor, genre):

    api_query = f'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&api_key={api_key}'


    if director != "none":
        director = get_person_id(director)
        api_query = api_query + f"&with_crew={director}"

    if actor != "none":
        actor = get_person_id(actor)
        api_query = api_query + f"&with_cast={actor}"
    
    if genre != "none":
        genre = genre_dict[genre.lower()]
        api_query = api_query + f"&with_genres={genre}"
        
    r = requests.get(api_query)
    results = json.loads(r.text)['results']

    if results == []:
        return Response("No movies matching those details were found")
    
    movie_details = f"I've found {len(results)} movies for you. How does {results[0]['title']} sound? It has a rating of {round(results[0]['vote_average'],2)}."
    return Response(movie_details)

def get_person_id(person_query):
    # find the person ID in the movie API so that we can query movies with that person
    api_query = f'https://api.themoviedb.org/3/search/person?api_key={api_key}&language=en-US&query={person_query}'
    
    r = requests.get(api_query)
    results = json.loads(r.text)["results"]
    if results == []:
        # no person with that name is the movie API database
        return None
    return results[0]['id']