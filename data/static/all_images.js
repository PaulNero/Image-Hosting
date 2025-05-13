document.addEventListener('DOMContentLoaded', function() {
    let currentImageIndex = 0;
    let images = [];
    let currentPage = 1;
    let isLoading = false;
    let currentView = 'gallery'; // 'gallery' или 'table'

    /**
     * Инициализация компонентов просмотра изображений
     * Создаем оверлей для предпросмотра и кнопки навигации
     */
    const previewOverlay = document.createElement('div');
    previewOverlay.className = 'preview-overlay';
    
    const previewImage = document.createElement('img');
    previewImage.className = 'preview-image';
    
    const leftArrow = document.createElement('button');
    leftArrow.className = 'nav-arrow left';
    leftArrow.innerHTML = '←';
    
    const rightArrow = document.createElement('button');
    rightArrow.className = 'nav-arrow right';
    rightArrow.innerHTML = '→';
    
    previewOverlay.appendChild(leftArrow);
    previewOverlay.appendChild(previewImage);
    previewOverlay.appendChild(rightArrow);
    document.body.appendChild(previewOverlay);

    /**
     * Настройка переключателей режимов отображения (галерея/таблица)
     */
    const galleryViewBtn = document.getElementById('gallery-view-btn');
    const tableViewBtn = document.getElementById('table-view-btn');
    
    // Базовое значение для галереи
    let imagesPerPage = 15;
    
    galleryViewBtn.addEventListener('click', () => {
        currentView = 'gallery';
        galleryViewBtn.classList.add('active');
        tableViewBtn.classList.remove('active');
        document.getElementById('images-gallery').style.display = 'grid';
        document.getElementById('images-table').style.display = 'none';
        
        // Устанавливаем количество изображений для галереи
        imagesPerPage = 15;
        // Обновляем изображения при переключении вида
        loadImages(1);
    });
    
    tableViewBtn.addEventListener('click', () => {
        currentView = 'table';
        tableViewBtn.classList.add('active');
        galleryViewBtn.classList.remove('active');
        document.getElementById('images-gallery').style.display = 'none';
        document.getElementById('images-table').style.display = 'table';
        
        // Устанавливаем большее количество изображений для таблицы
        imagesPerPage = 25;
        // Обновляем изображения при переключении вида
        loadImages(1);
    });

    /**
     * Показывает изображение в режиме предпросмотра
     * 
     * @param {number} index - Индекс изображения в массиве images
     */
    function showPreview(index) {
        currentImageIndex = index;
        previewImage.src = `/images/${images[index].filename}`;
        previewOverlay.style.display = 'flex';
    }

    /**
     * Скрывает предпросмотр изображения
     */
    function hidePreview() {
        previewOverlay.style.display = 'none';
    }

    /**
     * Показывает следующее изображение в режиме предпросмотра
     * При достижении конца списка переходит к первому изображению
     */
    function showNextImage() {
        if (currentImageIndex < images.length - 1) {
            showPreview(currentImageIndex + 1);
        } else {
            // Циклическая навигация - переходим к первому изображению
            showPreview(0);
        }
    }

    /**
     * Показывает предыдущее изображение в режиме предпросмотра
     * При достижении начала списка переходит к последнему изображению
     */
    function showPreviousImage() {
        if (currentImageIndex > 0) {
            showPreview(currentImageIndex - 1);
        } else {
            // Циклическая навигация - переходим к последнему изображению
            showPreview(images.length - 1);
        }
    }

    /**
     * Настройка обработчиков событий для предпросмотра
     */
    previewOverlay.addEventListener('click', (e) => {
        if (e.target === previewOverlay) {
            hidePreview();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (previewOverlay.style.display === 'flex') {
            if (e.key === 'Escape') {
                hidePreview();
            } else if (e.key === 'ArrowLeft') {
                showPreviousImage();
            } else if (e.key === 'ArrowRight') {
                showNextImage();
            }
        }
    });

    leftArrow.addEventListener('click', (e) => {
        e.stopPropagation();
        showPreviousImage();
    });

    rightArrow.addEventListener('click', (e) => {
        e.stopPropagation();
        showNextImage();
    });

    /**
     * Форматирует дату в локализованный формат для отображения
     * 
     * @param {string} dateString - ISO строка даты или timestamp
     * @returns {string} Отформатированная дата в формате DD.MM.YYYY HH:MM
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Форматирует размер файла в килобайты с округлением до 2 знаков
     * 
     * @param {number} bytes - Размер файла в байтах
     * @returns {string} Размер файла в КБ с округлением до 2 знаков
     */
    function formatFileSize(bytes) {
        return (bytes / 1024).toFixed(2);
    }

    /**
     * Удаляет изображение по имени файла через API (старый метод)
     * 
     * @param {string} filename - Имя файла для удаления
     * @returns {Promise<void>}
     */
    async function deleteImageByFilename(filename) {
        if (confirm('Вы уверены, что хотите удалить это изображение?')) {
            try {
                const response = await fetch(`/api/images/${filename}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    // Обновляем массив изображений
                    images = images.filter(img => img.filename !== filename);
                    
                    // Обновляем отображение
                    renderAllImages();
                } else {
                    alert('Ошибка при удалении изображения');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка при удалении изображения');
            }
        }
    }
    
    /**
     * Удаляет изображение по ID через API (новый метод по ТЗ)
     * 
     * @param {number} id - ID изображения для удаления
     * @returns {Promise<void>}
     */
    async function deleteImageById(id) {
        if (confirm('Вы уверены, что хотите удалить это изображение?')) {
            try {
                // Используем GET-запрос к маршруту /delete/<id>
                window.location.href = `/delete/${id}`;
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка при удалении изображения');
            }
        }
    }

    /**
     * Загружает изображения с пагинацией
     * 
     * @param {number} page - Номер страницы (начиная с 1)
     * @returns {Promise<void>}
     */
    async function loadImages(page = 1) {
        if (isLoading) return;
        isLoading = true;
        
        // Добавляем элемент для отображения ошибок
        const errorContainer = document.getElementById('error-container') || 
            (() => {
                const container = document.createElement('div');
                container.id = 'error-container';
                container.style.color = 'red';
                container.style.padding = '10px';
                container.style.margin = '10px 0';
                container.style.display = 'none';
                // Добавляем контейнер перед галереей
                const galleryContainer = document.getElementById('images-gallery');
                galleryContainer.parentNode.insertBefore(container, galleryContainer);
                return container;
            })();
        
        // Скрываем сообщение об ошибке при новой загрузке
        errorContainer.style.display = 'none';

        try {
            // Передаем параметр per_page со значением imagesPerPage
            const response = await fetch(`/api/images?page=${page}&per_page=${imagesPerPage}`);
            
            if (!response.ok) {
                throw new Error(`Ошибка загрузки: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (page === 1) {
                images = data.images;
            } else {
                // Проверяем, есть ли новые изображения
                if (data.images.length === 0) {
                    isLoading = false;
                    return;
                }
                images = [...images, ...data.images];
            }

            renderAllImages();
            currentPage = page;
        } catch (error) {
            console.error('Ошибка загрузки изображений:', error);
            
            // Показываем сообщение об ошибке пользователю
            errorContainer.textContent = `Не удалось загрузить изображения: ${error.message}`;
            errorContainer.style.display = 'block';
            
            // Если это первая страница и произошла ошибка, показываем пустое состояние
            if (page === 1) {
                const galleryContainer = document.getElementById('images-gallery');
                galleryContainer.innerHTML = '<p class="no-images">Не удалось загрузить изображения. Попробуйте обновить страницу.</p>';
            }
        } finally {
            isLoading = false;
        }
    }
    
    /**
     * Отрисовывает все изображения в текущем режиме отображения
     * Обновляет оба контейнера: галерею и таблицу
     */
    function renderAllImages() {
        // Очищаем оба контейнера
        const galleryContainer = document.getElementById('images-gallery');
        const tableBody = document.getElementById('table-body');
        
        galleryContainer.innerHTML = '';
        tableBody.innerHTML = '';
        
        if (!images || images.length === 0) {
            galleryContainer.innerHTML = '<p class="no-images">Нет загруженных изображений</p>';
            return;
        }
        
        // Рендерим галерею
        renderGallery();
        
        // Рендерим таблицу
        renderTable();
    }

    /**
     * Отображает изображения в виде галереи
     * Создает сетку с изображениями и кнопками удаления
     */
    function renderGallery() {
        const galleryContainer = document.getElementById('images-gallery');
        
        images.forEach((image, index) => {
            const container = document.createElement('div');
            container.className = 'image-container';
            container.setAttribute('data-filename', image.filename);
            container.setAttribute('data-id', image.id);

            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete-button';
            deleteButton.innerHTML = '🗑️';
            deleteButton.onclick = (e) => {
                e.stopPropagation();
                deleteImageById(image.id);
            };

                const a = document.createElement('a');
            a.href = '#';
            a.onclick = (e) => {
                e.preventDefault();
                showPreview(index);
            };

                const imageElement = document.createElement('img');
            imageElement.src = `/images/${image.filename}`;
            imageElement.alt = image.original_name || image.filename;
            imageElement.style.maxWidth = '100%';
            imageElement.style.maxHeight = '100%';
                imageElement.style.objectFit = 'contain';

                a.appendChild(imageElement);
            container.appendChild(deleteButton);
            container.appendChild(a);
                
                const caption = document.createElement('div');
            caption.textContent = image.original_name || image.filename;
                caption.style.marginTop = '5px';
                caption.style.wordBreak = 'break-all';
                caption.style.fontSize = '12px';
                caption.style.color = '#666';
                container.appendChild(caption);

            galleryContainer.appendChild(container);
        });
    }
    
    /**
     * Отображает изображения в виде таблицы
     * Создает строки с информацией о каждом изображении и кнопками действий
     */
    function renderTable() {
        const tableBody = document.getElementById('table-body');
        
        images.forEach((image, index) => {
            const row = document.createElement('tr');
            
            // Превью
            const thumbnailCell = document.createElement('td');
            const thumbnail = document.createElement('img');
            thumbnail.src = `/images/${image.filename}`;
            thumbnail.alt = image.original_name || image.filename;
            thumbnail.className = 'thumbnail';
            thumbnailCell.appendChild(thumbnail);
            
            // Имя файла
            const filenameCell = document.createElement('td');
            const filenameLink = document.createElement('a');
            filenameLink.href = `/images/${image.filename}`;
            filenameLink.textContent = image.filename;
            filenameLink.target = '_blank';
            filenameCell.appendChild(filenameLink);
            
            // Оригинальное имя
            const originalNameCell = document.createElement('td');
            originalNameCell.textContent = image.original_name;
            
            // Размер (КБ)
            const sizeCell = document.createElement('td');
            sizeCell.textContent = formatFileSize(image.size) + ' КБ';
            
            // Дата загрузки
            const uploadTimeCell = document.createElement('td');
            uploadTimeCell.textContent = formatDate(image.upload_time);
            
            // Тип файла
            const fileTypeCell = document.createElement('td');
            fileTypeCell.textContent = image.file_type;
            
            // Действия
            const actionsCell = document.createElement('td');
            actionsCell.className = 'table-actions';
            
            // Кнопка просмотра
            const viewBtn = document.createElement('button');
            viewBtn.className = 'view-btn';
            viewBtn.textContent = '👁️';
            viewBtn.title = 'Просмотреть';
            viewBtn.onclick = () => showPreview(index);
            
            // Кнопка удаления
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.textContent = '🗑️';
            deleteBtn.title = 'Удалить';
            deleteBtn.onclick = () => deleteImageById(image.id);
            
            actionsCell.appendChild(viewBtn);
            actionsCell.appendChild(deleteBtn);
            
            // Добавляем ячейки в строку
            row.appendChild(thumbnailCell);
            row.appendChild(filenameCell);
            row.appendChild(originalNameCell);
            row.appendChild(sizeCell);
            row.appendChild(uploadTimeCell);
            row.appendChild(fileTypeCell);
            row.appendChild(actionsCell);
            
            // Добавляем строку в таблицу
            tableBody.appendChild(row);
        });
    }

    /**
     * Настройка бесконечной прокрутки для ленивой загрузки изображений
     * Загружает следующую страницу при прокрутке к нижней части страницы
     */
    let lastScrollTime = 0;
    const scrollThrottle = 500; // Задержка между запросами в миллисекундах

    window.addEventListener('scroll', () => {
        const currentTime = Date.now();
        if (currentTime - lastScrollTime < scrollThrottle) return;
        lastScrollTime = currentTime;

        // Проверяем, достигли ли мы нижней части страницы
        const scrollPosition = window.innerHeight + window.scrollY;
        const documentHeight = document.documentElement.scrollHeight;
        
        if (scrollPosition >= documentHeight - 1000 && !isLoading) {
            loadImages(currentPage + 1);
        }
    });

    // Начальная загрузка изображений
    loadImages(1);
});