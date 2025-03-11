document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/images')
        .then(response => response.json())
        .then(data => {
            const imagesContainer = document.getElementById('images');
            if (!data.images || data.images.length === 0) {
                imagesContainer.innerHTML = '<p>Нет загруженных изображений</p>';
                return;
            }

            data.images.forEach(image => {
                const container = document.createElement('div');
                container.style.display = 'inline-block';
                container.style.margin = '10px';
                container.style.textAlign = 'center';

                const a = document.createElement('a');
                a.href = `/images/${image}`;
                a.target = '_blank';
                container.appendChild(a);

                const imageElement = document.createElement('img');
                imageElement.src = `/images/${image}`;
                imageElement.alt = image;
                imageElement.style.maxWidth = '200px';
                imageElement.style.maxHeight = '200px';
                imageElement.style.objectFit = 'contain';
                imageElement.style.border = '1px solid #ddd';
                imageElement.style.borderRadius = '4px';
                imageElement.style.padding = '5px';

                a.appendChild(imageElement);
                
                const caption = document.createElement('div');
                caption.textContent = image;
                caption.style.marginTop = '5px';
                caption.style.wordBreak = 'break-all';
                caption.style.maxWidth = '200px';
                caption.style.fontSize = '12px';
                caption.style.color = '#666';
                container.appendChild(caption);

                imagesContainer.appendChild(container);
            });
        })
        .catch(error => {
            console.error('Error fetching images:', error);
            const imagesContainer = document.getElementById('images');
            imagesContainer.innerHTML = '<p style="color: red;">Ошибка загрузки изображений</p>';
        });
});