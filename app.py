#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import ( 
 Flask,
 render_template,
 request, 
 Response, 
 flash, 
 redirect, 
 url_for,
 jsonify
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import text
from datetime import datetime
from models import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# DONE: connect to a local postgresql database
migrate = Migrate(app= app, db= db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
@app.route('/home')
def index():
    # I'll use id to sort them since it's serial!
    try:
        Venues = venue.query.order_by(db.desc(venue.id)).limit(10).all()
        Artists = artist.query.order_by(db.desc(artist.id)).limit(10).all()
    except:
        print(sys.exc_info())
        Venues = []
        Artists = []
    return render_template('pages/home.html', venues = Venues, artists = Artists)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # DONE: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    try:
        cities_states = venue.query.with_entities(venue.city, venue.state).group_by(venue.city, venue.state).all() # all unique pairs {city, state}
        venues = [] # store venues for each pair
        venue_data = [] # the list we pass to the render_template
        
        for city_state in cities_states: # for each pair
            dic = {}        # to store each venue required data 
            dic['city'] = city_state[0]
            dic['state'] = city_state[1]
            venue_data.append(dic)      # append it to the list
            # in the next line I get venues with the pair city_state
            try:
                vens = venue.query.with_entities(venue.id, venue.name).filter(venue.city == city_state[0] , venue.state == city_state[1]).all()
            except:
                vens = []
            # append those venues to a list to use them to get number of upcoming shows
            venues.append(vens)

        # iterate through retrieved venues and calculate number of upcoming shows per each
        for i,ven in zip(range(len(venues)),venues):
            # venues length equal to number of unique pairs {city_state}
            venues_list = []   # stores venues required data for each pair 
            for each in ven:
                dic = {}
                try:
                    dic['num_upcoming_shows'] = show.query.filter(show.venue_id == each[0], show.start_date > date.now()).count()
                except:
                    dic['num_upcoming_shows'] = 0
                dic['id'] = each[0]
                dic['name'] = each[1]
                venues_list.append(dic)
            # now venues_list contains all the venues with the ith {city, state} pair
            # so I store it in the list that will be passed to render_template
            venue_data[i]['venues'] = venues_list  
            
        return render_template('pages/venues.html', areas=venue_data)
    except Exception as e:
        print(e)
        flash('something went wrong!')
        return redirect('/')

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    reg = '%'+request.form.get('search_term')+'%'
    req_venues = venue.query.with_entities(venue.id,venue.name).filter(venue.name.ilike(reg)).all()
    data = []
    for ven in req_venues:
        dic = {}
        dic['id'] = ven[0]
        dic['name'] = ven[1]
        data.append(dic)

    response = {
      'count':len(req_venues),
      'data': data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # DONE: replace with real venue data from the venues table, using venue_id
    # https://docs.python.org/3/library/datetime.html#datetime.date.strftime
    try:
        venue_data = venue.query.get(venue_id)
        # I think the query is complex!
        shows = show.query.with_entities(venue, artist.id, artist.name, artist.image_link, show.start_date).join(venue).join(artist).filter(venue.id == venue_id).all()
        past_shows = list(filter(lambda x: x.start_date < datetime.now(), shows))
        upcoming_shows = list(filter(lambda x: x.start_date >= datetime.now(), shows))
        
        def show_artist(showObj):
            dec = {}
            dec['artist_id'] = showObj.id
            dec['artist_name'] = showObj.name
            dec['artist_image_link'] = showObj.image_link
            dec['start_date'] = showObj.start_date.strftime("%Y-%m-%d %H:%M:%S")
            return dec
        past_shows = list(map(lambda x: show_artist(x), past_shows))
        upcoming_shows = list(map(lambda x: show_artist(x), upcoming_shows))

        data={
          "id":venue_data.id,
          "name":venue_data.name,
          "genres": venue_data.genres.split(','),
          "address": venue_data.address,
          "city": venue_data.city,
          "state": venue_data.state,
          "phone": venue_data.phone,
          "website": venue_data.website,
          "facebook_link": venue_data.facebook_link,
          "seeking_talent": venue_data.seeking_talent,
          "seeking_description": venue_data.seeking_description,
          "image_link": venue_data.image_link,
          "past_shows": past_shows,
          "upcoming_shows": upcoming_shows,
          "past_shows_count": len(past_shows),
          "upcoming_shows_count": len(upcoming_shows)
        }
        return render_template('pages/show_venue.html', venue=data)
    except Exception as e:
        print(e)
        return redirect('/venues')
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # DONE: insert form data as a new Venue record in the db, instead
    # DONE : modify data to be the data object returned from db insertion
    form = VenueForm(request.form)
    if form.validate_on_submit():
        try:
            venue_obj = venue()
            if form.image_link.data == '':
                form.image_link.data = 'https://images.pond5.com/music-venue-word-cloud-animated-footage-107230910_iconl.jpeg'
            
            form.populate_obj(venue_obj)
            venue_obj.genres = ', '.join(form.genres.data)
            db.session.add(venue_obj)
            db.session.commit()
            flash('Venue ' + venue_obj.name + ' was successfully listed!')
        except:
            print(sys.exc_info())
            db.session.rollback()
            flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        finally:
            db.session.close()
        return redirect('/venues')
    else:
        for key in form.errors:
            flash(key +" : "+' '.join(form.errors[key]))
        return render_template('forms/new_venue.html', form=VenueForm())
    
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # DONE: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    print(venue_id)
    try:
        venue.query.filter_by(id = venue_id).delete()
        db.session.commit()
        db.session.close()
        flash('The Venue was deleted successfully!.')
        return jsonify({'success': True}) 
    except Exception as e:
        print(e)
        db.session.rollback()
        flash('An error occurred. could not delete the venue.')
        db.session.close()
        return jsonify({'success': False}) 

     

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # DONE: replace with real data returned from querying the database
    req_artists = artist.query.with_entities(artist.id,artist.name).all()
    data = []
    for art in req_artists:
        dec = {}
        dec['id'] = art[0]
        dec['name'] = art[1]
        data.append(dec)

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    reg = '%'+request.form.get('search_term')+'%'
    req_artists = artist.query.with_entities(artist.id,artist.name).filter(artist.name.ilike(reg)).all()
    data = []
    for art in req_artists:
        dic = {}
        dic['id'] = art[0]
        dic['name'] = art[1]
        data.append(dic)

    response = {
      'count':len(req_artists),
      'data': data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # DONE: replace with real venue data from the venues table, using venue_id 
        
    
    try:
        artist_data = artist.query.get(artist_id)
        # using join to get shows data as well as venue data for that artist! 
        shows = show.query.with_entities(artist, venue.id, venue.name, venue.image_link, show.start_date).join(venue).join(artist).filter(artist.id == artist_id).all()
        past_shows = list(filter(lambda x: x.start_date < datetime.now(), shows))
        upcoming_shows = list(filter(lambda x: x.start_date >= datetime.now(), shows))
        
        def show_artist(showObj):
            dec = {}
            dec['venue_id'] = showObj.id
            dec['venue_name'] = showObj.name
            dec['venue_image_link'] = showObj.image_link
            dec['start_date'] = showObj.start_date.strftime("%Y-%m-%d %H:%M:%S")
            return dec
        past_shows = list(map(lambda x: show_artist(x), past_shows))
        upcoming_shows = list(map(lambda x: show_artist(x), upcoming_shows))

        data={
          "id": artist_data.id,
          "name":artist_data.name,
          "genres": artist_data.genres.split(','),
          "city": artist_data.city,
          "state": artist_data.state,
          "phone": artist_data.phone,
          "website": artist_data.website,
          "facebook_link": artist_data.facebook_link,
          "seeking_talent": artist_data.seeking_venue,
          "seeking_description": artist_data.seeking_description,
          "image_link": artist_data.image_link,
          "past_shows": past_shows,
          "upcoming_shows": upcoming_shows,
          "past_shows_count": len(past_shows),
          "upcoming_shows_count": len(upcoming_shows)
        }

        return render_template('pages/show_artist.html', artist=data)
    except :
        print(sys.exc_info())
        return redirect('/artists')
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # DONE: populate form with fields from artist with ID <artist_id>
    form = ArtistForm()
    data = artist.query.get(artist_id)
    try:
        artist_data={
          "id": data.id,
          "name": data.name,
          "genres": data.genres.split(','),
          "city": data.city,
          "state": data.state,
          "phone": data.phone,
          "website": data.website,
          "facebook_link": data.facebook_link,
          "seeking_venue": data.seeking_venue,
          "seeking_description": data.seeking_description,
          "image_link": data.image_link
        }
        form.genres.data = artist_data['genres']
        return render_template('forms/edit_artist.html', form=form, artist = artist_data)

    except :
        print(sys.exc_info())
        return redirect('/artists/'+str(artist_id))

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
      # venue record with ID <venue_id> using the new attributes
    form = ArtistForm(request.form)
    if form.validate_on_submit():
        try:
            # Default image
            if form.image_link.data == '':
                form.image_link.data = 'https://cdn.pixabay.com/photo/2018/04/18/18/56/user-3331257__340.png'

            artist_obj = artist.query.get(artist_id)
                
            artist_obj.name = form.name.data
            artist_obj.city = form.city.data
            artist_obj.state = form.state.data
            artist_obj.phone = form.phone.data
            artist_obj.genres = ', '.join(form.genres.data)
            artist_obj.facebook_link = form.facebook_link.data
            artist_obj.website = form.website.data
            artist_obj.seeking_description = form.seeking_description.data
            artist_obj.seeking_venue = form.seeking_venue.data
            artist_obj.image_link = form.image_link.data
            db.session.commit()
            flash('Artist ' + artist_obj.name + ' was successfully edited!')
        except:
            print(sys.exc_info())
            db.session.rollback()
            flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
        finally:
            db.session.close()
        return redirect('/artists/'+str(artist_id))
    else:
        for key in form.errors:
            flash(key +" : "+' '.join(form.errors[key]))
        return redirect('/artists/'+str(artist_id)+'/edit')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    data = venue.query.get(venue_id).__dict__
    try:
        venue_data={
          "id": data['id'],
          "name": data['name'],
          "genres": data['genres'].replace(", ", ",").split(','),
          "city": data['city'],
          "state": data['state'],
          "address": data['address'],
          "phone": data['phone'],
          "website": data['website'],
          "facebook_link": data['facebook_link'],
          "seeking_talent": data['seeking_talent'],
          "seeking_description": data['seeking_description'],
          "image_link": data['image_link']
        }
        form.genres.data = venue_data['genres']

        return render_template('forms/edit_venue.html', form=form, venue = venue_data)

    except :
        print(sys.exc_info())
        return redirect('/venues/'+str(venue_id))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # DONE: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    if form.validate_on_submit():
        try:
            # Default image
            if form.image_link.data == '':
                form.image_link.data = 'https://images.pond5.com/music-venue-word-cloud-animated-footage-107230910_iconl.jpeg'

            venue_obj = venue.query.get(venue_id)
                
            venue_obj.name = form.name.data
            venue_obj.city = form.city.data
            venue_obj.state = form.state.data
            venue_obj.phone = form.phone.data
            venue_obj.address = form.address.data
            venue_obj.genres = ', '.join(form.genres.data)
            venue_obj.facebook_link = form.facebook_link.data
            venue_obj.website = form.website.data
            venue_obj.seeking_description = form.seeking_description.data
            venue_obj.seeking_talent = form.seeking_talent.data
            venue_obj.image_link = form.image_link.data
            db.session.commit()
            flash('Venue ' + venue_obj.name + ' was successfully edited!')
        except:
            print(sys.exc_info())
            db.session.rollback()
            flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
        finally:
            db.session.close()
        return redirect('/venues/'+str(venue_id))     
    else:
        for key in form.errors:
            flash(key +" : "+' '.join(form.errors[key]))
        return redirect('/venues/'+str(venue_id)+'/edit')
    
        
    

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)
    if form.validate_on_submit():
        try:
            artist_obj = artist()
            # default image
            if form.image_link.data == '':
                form.image_link.data = 'https://cdn.pixabay.com/photo/2018/04/18/18/56/user-3331257__340.png'
            form.populate_obj(artist_obj)
            artist_obj.genres = ', '.join(form.genres.data)
            db.session.add(artist_obj)
            db.session.commit()
            flash('Artist ' + artist_obj.name + ' was successfully listed!')
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        finally:
            db.session.close()
        return redirect('/artists')
    else:
        for key in form.errors:
            flash(key +" : "+' '.join(form.errors[key]))
        return render_template('forms/new_artist.html', form=ArtistForm())


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # DONE: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    try:
        shows = show.query.with_entities(venue.id, venue.name, artist.id, artist.name, artist.image_link, show.start_date).join(venue).join(artist).all()
    except:
        print(sys.exc_info())
        shows = []
    data = []
    for each in shows:
        dic = {}
        dic['venue_id'] = each[0]
        dic['venue_name'] = each[1]
        dic['artist_id'] = each[2]
        dic['artist_name'] = each[3]
        dic['artist_image_link'] = each[4]
        dic['start_date'] = each[5].strftime("%Y-%m-%d %H:%M:%S")
        data.append(dic)

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # DONE: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)
    if form.validate_on_submit():
        try:
            show_obj = show()
            form.populate_obj(show_obj)
            db.session.add(show_obj)
            db.session.commit()
            flash('The Show was successfully listed!')
            return redirect('/')

        except :
            print(sys.exc_info())
            flash('An error occurred. Show could not be listed, make sure the venue and the artist exist!')
            db.session.rollback()
            db.session.close()
            return redirect('/shows/create')
    else:
        for key in form.errors:
            flash(key +" : "+' '.join(form.errors[key]))
        return render_template('forms/new_show.html', form=ShowForm())

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
