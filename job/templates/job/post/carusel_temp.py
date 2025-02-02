<div class="container">
    <div class="row g-5">
        <div class="col-lg-6 col-sm-12 mb-5">
            <p class="fs-5 text-center">Наши объекты:</p>

            <div id="carouselExampleAutoplaying" class="carousel slide my-carousel" data-bs-ride="carousel">
                <div class="carousel-inner">
                    {% for post in posts %}
                    <div class="carousel-item {% if forloop.first %}active{% endif %}">
                        {% if post.photo %}
                            <p><img class="custom-image img-fluid" src="{{post.photo.url}}"></p>
                        {% else %}
                            <p><img class="custom-image img-fluid" src="{% static 'job/images/default-image.jpg' %}" alt="Description"></p>
                        {% endif %}
                        <div class="carousel-caption d-none d-md-block">
                            <h5>{{ post.title }}</h5>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleAutoplaying"
                        data-bs-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span> <span
                        class="visually-hidden">Previous</span>
                </button>

                <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleAutoplaying"
                        data-bs-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true"></span> <span
                        class="visually-hidden">Next</span>
                </button>
            </div>
        </div>
    </div>
</div>