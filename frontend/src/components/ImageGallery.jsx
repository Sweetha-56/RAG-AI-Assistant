import { buildImageUrl } from "../services/api";

export default function ImageGallery({ imagePaths = [] }) {
  if (!imagePaths || imagePaths.length === 0) {
    return (
      <section className="panel-card detail-card">
        <div className="panel-card-header">
          <h3>Related Images</h3>
        </div>
        <div className="empty-state">No related images available.</div>
      </section>
    );
  }

  return (
    <section className="panel-card detail-card">
      <div className="panel-card-header">
        <h3>Related Images</h3>
      </div>

      <div className="image-gallery">
        {imagePaths.map((path, index) => (
          <div key={`${path}-${index}`} className="image-gallery-item">
            <img
              src={buildImageUrl(path)}
              alt={`Retrieved visual ${index + 1}`}
              className="result-image"
            />
            <div className="image-path">{path}</div>
          </div>
        ))}
      </div>
    </section>
  );
}